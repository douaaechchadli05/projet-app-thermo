"""
Routes de calcul pour l'application thermodynamique
Gère les calculs de la loi de Raoult et l'historique utilisateur
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField
from wtforms.validators import DataRequired, NumberRange

from models.calcul import Calcul
from services.security_service import security_service

# Création du blueprint pour les routes de calcul
calcul_bp = Blueprint('calcul', __name__)

# Formulaire de calcul
class CalculForm(FlaskForm):
    """Formulaire pour les calculs thermodynamiques"""
    x1_benzene = FloatField('Benzène (%)', 
                           validators=[DataRequired(), NumberRange(min=0, max=100)])
    x2_toluene = FloatField('Toluène (%)', 
                           validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Calculer')

@calcul_bp.route('/calcul', methods=['GET', 'POST'])
@login_required
def calcul_page():
    """
    Page principale de calcul de la loi de Raoult
    """
    form = CalculForm()
    results = None
    
    if form.validate_on_submit():
        x1_benzene = form.x1_benzene.data
        x2_toluene = form.x2_toluene.data
        
        # Valider que les fractions molaires sont correctes
        is_valid, error_message = Calcul.valider_fractions(x1_benzene, x2_toluene)
        
        if not is_valid:
            flash(error_message, 'danger')
        else:
            try:
                # Créer et sauvegarder le calcul
                calcul = Calcul(
                    user_id=current_user.id,
                    x1_benzene=x1_benzene,
                    x2_toluene=x2_toluene
                )
                
                from app_complete import db
                db.session.add(calcul)
                db.session.commit()
                
                # Préparer les résultats pour l'affichage
                results = calcul.get_results_dict()
                
                flash('Calcul effectué avec succès !', 'success')
                
            except Exception as e:
                current_app.logger.error(f"Erreur lors du calcul: {e}")
                flash('Une erreur est survenue lors du calcul.', 'danger')
                from app_complete import db
                db.session.rollback()
    
    # Récupérer l'historique de l'utilisateur
    user_history = Calcul.get_user_calculs(current_user.id, limit=10)
    
    return render_template(
        'calcul/calcul.html',
        form=form,
        results=results,
        history=user_history,
        constants={
            'P1_SAT': Calcul.P1_SAT,
            'P2_SAT': Calcul.P2_SAT,
            'TEMPERATURE': 80.0
        }
    )

@calcul_bp.route('/api/calcul', methods=['POST'])
@login_required
def api_calcul():
    """
    API pour effectuer un calcul (format JSON)
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Aucune donnée fournie'}), 400
        
        x1_benzene = float(data.get('x1_benzene', 0))
        x2_toluene = float(data.get('x2_toluene', 0))
        
        # Valider les données
        is_valid, error_message = Calcul.valider_fractions(x1_benzene, x2_toluene)
        
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        # Effectuer le calcul
        calcul = Calcul(
            user_id=current_user.id,
            x1_benzene=x1_benzene,
            x2_toluene=x2_toluene
        )
        
        from app_complete import db
        db.session.add(calcul)
        db.session.commit()
        
        return jsonify(calcul.get_results_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"Erreur API calcul: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@calcul_bp.route('/history')
@login_required
def history():
    """
    Page d'historique détaillé des calculs
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Pagination des calculs
    pagination = Calcul.query.filter_by(user_id=current_user.id)\
                           .order_by(Calcul.created_at.desc())\
                           .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'calcul/history.html',
        pagination=pagination,
        calculs=pagination.items
    )

@calcul_bp.route('/calcul/<int:calcul_id>')
@login_required
def calcul_detail(calcul_id):
    """
    Page de détail d'un calcul spécifique
    """
    calcul = Calcul.query.filter_by(id=calcul_id, user_id=current_user.id).first()
    
    if not calcul:
        flash('Calcul non trouvé.', 'danger')
        return redirect(url_for('calcul.history'))
    
    return render_template('calcul/calcul_detail.html', calcul=calcul)

@calcul_bp.route('/calcul/<int:calcul_id>/delete', methods=['POST'])
@login_required
def delete_calcul(calcul_id):
    """
    Supprimer un calcul spécifique
    """
    calcul = Calcul.query.filter_by(id=calcul_id, user_id=current_user.id).first()
    
    if not calcul:
        flash('Calcul non trouvé.', 'danger')
        return redirect(url_for('calcul.history'))
    
    try:
        from app_complete import db
        db.session.delete(calcul)
        db.session.commit()
        
        flash('Calcul supprimé avec succès.', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la suppression du calcul: {e}")
        flash('Erreur lors de la suppression du calcul.', 'danger')
        from app_complete import db
        db.session.rollback()
    
    return redirect(url_for('calcul.history'))

@calcul_bp.route('/statistics')
@login_required
def statistics():
    """
    Page de statistiques personnelles
    """
    stats = Calcul.get_statistics(current_user.id)
    
    # Calculs récents
    recent_calculs = Calcul.get_user_calculs(current_user.id, limit=5)
    
    # Distribution des pressions de bulle
    pressure_distribution = {}
    for calcul in Calcul.get_user_calculs(current_user.id, limit=100):
        pressure_range = int(calcul.p_bulle / 10) * 10  # Regrouper par tranche de 10 kPa
        key = f"{pressure_range}-{pressure_range + 10} kPa"
        pressure_distribution[key] = pressure_distribution.get(key, 0) + 1
    
    return render_template(
        'calcul/statistics.html',
        stats=stats,
        recent_calculs=recent_calculs,
        pressure_distribution=pressure_distribution
    )

@calcul_bp.route('/export')
@login_required
def export_data():
    """
    Exporter les données de calcul de l'utilisateur
    """
    import csv
    from io import StringIO
    from flask import Response
    
    # Récupérer tous les calculs de l'utilisateur
    calculs = Calcul.get_user_calculs(current_user.id, limit=1000)
    
    # Créer le CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow([
        'ID', 'Date', 'Benzène (%)', 'Toluène (%)', 
        'Pression bulle (kPa)', 'y1', 'y2', 'Somme y_i', 'Vérification'
    ])
    
    # Données
    for calcul in calculs:
        results = calcul.get_results_dict()
        writer.writerow([
            calcul.id,
            calcul.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            calcul.x1_benzene,
            calcul.x2_toluene,
            results['p_bulle'],
            results['y1'],
            results['y2'],
            results['sum_yi'],
            'OK' if results['verification'] else 'ERREUR'
        ])
    
    # Créer la réponse
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=calculs_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )

@calcul_bp.route('/theory')
def theory():
    """
    Page expliquant la théorie de la loi de Raoult
    """
    return render_template('calcul/theory.html')

@calcul_bp.route('/help')
def help():
    """
    Page d'aide pour l'utilisation du calculateur
    """
    return render_template('calcul/help.html')

# Gestion des erreurs pour les routes de calcul
@calcul_bp.errorhandler(404)
def calcul_not_found(error):
    """Gestion des erreurs 404 pour les calculs"""
    return render_template('errors/404.html'), 404

@calcul_bp.errorhandler(500)
def calcul_server_error(error):
    """Gestion des erreurs 500 pour les calculs"""
    from app_complete import db
    db.session.rollback()
    return render_template('errors/500.html'), 500
