"""
Routes administratives pour l'application
Gestion du dashboard, heatmap, utilisateurs et statistiques
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

from models.user import User
from models.admin import Admin
from models.calcul import Calcul
from models.security_log import SecurityLog
from models.ddos_attempts import DDOSAttempts
from services.heatmap_service import heatmap_service
from services.security_service import security_service

# Création du blueprint pour les routes administratives
admin_bp = Blueprint('admin', __name__)

# Décorateur pour vérifier les droits admin
def admin_required(f):
    """Décorateur pour exiger les droits d'administrateur"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Accès non autorisé.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Formulaires administratifs
class UserActionForm(FlaskForm):
    """Formulaire pour les actions sur les utilisateurs"""
    user_id = StringField('ID Utilisateur', validators=[DataRequired()])
    submit = SubmitField('Valider')

class NotificationForm(FlaskForm):
    """Formulaire pour envoyer des notifications"""
    subject = StringField('Sujet', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Envoyer')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """
    Tableau de bord administratif principal
    """
    # Créer une instance Admin pour accéder aux méthodes admin
    admin = Admin.query.get(current_user.id)
    
    # Statistiques générales
    stats = admin.get_statistics()
    
    # Activités récentes
    recent_logs = admin.get_security_logs(limit=10)
    
    # Calculs récents
    recent_calculs = admin.get_all_calculs(limit=10)
    
    # IP suspectes
    suspicious_ips = SecurityLog.get_suspicious_ips(hours=24, threshold=5)
    
    # Anomalies détectées
    anomalies = security_service.detect_anomalies(hours=24)
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_logs=recent_logs,
        recent_calculs=recent_calculs,
        suspicious_ips=suspicious_ips,
        anomalies=anomalies
    )

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """
    Page de gestion des utilisateurs
    """
    admin = Admin.query.get(current_user.id)
    
    # Filtres
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    verified_filter = request.args.get('verified', '')
    
    # Requête de base
    query = User.query
    
    # Appliquer les filtres
    if search:
        query = query.filter(
            (User.username.contains(search)) | 
            (User.email.contains(search))
        )
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    if verified_filter == 'verified':
        query = query.filter_by(is_verified=True)
    elif verified_filter == 'unverified':
        query = query.filter_by(is_verified=False)
    
    # Exclure l'admin actuel
    query = query.filter(User.id != current_user.id)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = query.order_by(User.created_at.desc())\
                     .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'admin/users.html',
        pagination=pagination,
        users=pagination.items,
        search=search,
        role_filter=role_filter,
        verified_filter=verified_filter
    )

@admin_bp.route('/user/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """
    Page de détail d'un utilisateur
    """
    admin = Admin.query.get(current_user.id)
    
    user = admin.get_user_by_id(user_id)
    if not user:
        flash('Utilisateur non trouvé.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Statistiques de l'utilisateur
    user_stats = Calcul.get_statistics(user_id)
    
    # Historique de sécurité
    security_history = admin.get_user_security_logs(user_id)
    
    # Calculs de l'utilisateur
    user_calculs = admin.get_user_calculs(user_id)
    
    return render_template(
        'admin/user_detail.html',
        user=user,
        user_stats=user_stats,
        security_history=security_history,
        user_calculs=user_calculs
    )

@admin_bp.route('/user/<int:user_id>/block', methods=['POST'])
@login_required
@admin_required
def block_user(user_id):
    """
    Bloquer un utilisateur
    """
    admin = Admin.query.get(current_user.id)
    
    if admin.block_user(user_id):
        flash('Utilisateur bloqué avec succès.', 'success')
        
        # Logger l'action
        security_service.log_security_event('user_blocked', current_user.id)
    else:
        flash('Erreur lors du blocage de l\'utilisateur.', 'danger')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/user/<int:user_id>/unblock', methods=['POST'])
@login_required
@admin_required
def unblock_user(user_id):
    """
    Débloquer un utilisateur
    """
    admin = Admin.query.get(current_user.id)
    
    if admin.unblock_user(user_id):
        flash('Utilisateur débloqué avec succès.', 'success')
        
        # Logger l'action
        security_service.log_security_event('user_unblocked', current_user.id)
    else:
        flash('Erreur lors du déblocage de l\'utilisateur.', 'danger')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """
    Supprimer un utilisateur et toutes ses données
    """
    admin = Admin.query.get(current_user.id)
    
    if admin.delete_user(user_id):
        flash('Utilisateur et ses données supprimés avec succès.', 'success')
        
        # Logger l'action
        security_service.log_security_event('user_deleted', current_user.id)
    else:
        flash('Erreur lors de la suppression de l\'utilisateur.', 'danger')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/heatmap')
@login_required
@admin_required
def heatmap():
    """
    Page de heatmap mondiale des connexions
    """
    admin = Admin.query.get(current_user.id)
    
    # Générer la heatmap
    days = request.args.get('days', 30, type=int)
    heatmap_html = heatmap_service.generate_world_heatmap(days=days)
    
    # Statistiques de connexion
    connection_stats = admin.get_heatmap_data(days=days)
    
    return render_template(
        'admin/heatmap.html',
        heatmap_html=heatmap_html,
        days=days,
        connection_stats=connection_stats
    )

@admin_bp.route('/heatmap/country')
@login_required
@admin_required
def heatmap_country():
    """
    Heatmap par pays
    """
    days = request.args.get('days', 30, type=int)
    heatmap_html = heatmap_service.generate_country_stats_map(days=days)
    
    return render_template(
        'admin/heatmap_country.html',
        heatmap_html=heatmap_html,
        days=days
    )

@admin_bp.route('/logs')
@login_required
@admin_required
def security_logs():
    """
    Page des logs de sécurité
    """
    admin = Admin.query.get(current_user.id)
    
    # Filtres
    action_filter = request.args.get('action', '')
    hours = request.args.get('hours', 24, type=int)
    
    # Requête de base
    query = SecurityLog.query
    
    # Filtre par action
    if action_filter:
        query = query.filter_by(action=action_filter)
    
    # Filtre par période
    from datetime import timedelta
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(SecurityLog.created_at >= since)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    pagination = query.order_by(SecurityLog.created_at.desc())\
                     .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'admin/security_logs.html',
        pagination=pagination,
        logs=pagination.items,
        action_filter=action_filter,
        hours=hours
    )

@admin_bp.route('/calculs')
@login_required
@admin_required
def all_calculs():
    """
    Page de tous les calculs utilisateurs
    """
    admin = Admin.query.get(current_user.id)
    
    # Filtres
    user_filter = request.args.get('user', '')
    days = request.args.get('days', 7, type=int)
    
    # Requête de base
    query = Calcul.query
    
    # Filtre par utilisateur
    if user_filter:
        query = query.join(User).filter(User.username.contains(user_filter))
    
    # Filtre par période
    from datetime import timedelta
    since = datetime.utcnow() - timedelta(days=days)
    query = query.filter(Calcul.created_at >= since)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    
    pagination = query.order_by(Calcul.created_at.desc())\
                     .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'admin/all_calculs.html',
        pagination=pagination,
        calculs=pagination.items,
        user_filter=user_filter,
        days=days
    )

@admin_bp.route('/ddos')
@login_required
@admin_required
def ddos_monitoring():
    """
    Page de monitoring DDoS
    """
    # IP bloquées
    blocked_ips = DDOSAttempts.get_blocked_ips()
    
    # IP suspectes
    suspicious_ips = DDOSAttempts.get_suspicious_ips(threshold=3, hours=24)
    
    # Statistiques DDoS
    ddos_stats = DDOSAttempts.get_statistics()
    
    return render_template(
        'admin/ddos_monitoring.html',
        blocked_ips=blocked_ips,
        suspicious_ips=suspicious_ips,
        ddos_stats=ddos_stats
    )

@admin_bp.route('/ddos/unblock/<ip_address>', methods=['POST'])
@login_required
@admin_required
def unblock_ip(ip_address):
    """
    Débloquer une IP
    """
    if DDOSAttempts.unblock_ip(ip_address):
        flash(f'IP {ip_address} débloquée avec succès.', 'success')
        
        # Logger l'action
        security_service.log_security_event('ip_unblocked', current_user.id)
    else:
        flash('Erreur lors du déblocage de l\'IP.', 'danger')
    
    return redirect(url_for('admin.ddos_monitoring'))

@admin_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
@admin_required
def notifications():
    """
    Page d'envoi de notifications administratives
    """
    form = NotificationForm()
    
    if form.validate_on_submit():
        from services.mail_service import mail_service
        
        # Envoyer la notification à tous les utilisateurs
        users = User.query.filter_by(role='user', is_verified=True).all()
        recipients = [user.email for user in users]
        
        if mail_service.send_admin_notification(
            subject=form.subject.data,
            message=form.message.data,
            recipients=recipients
        ):
            flash('Notification envoyée avec succès.', 'success')
        else:
            flash('Erreur lors de l\'envoi de la notification.', 'danger')
        
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/notifications.html', form=form)

@admin_bp.route('/export')
@login_required
@admin_required
def export_data():
    """
    Exporter les données du système
    """
    export_type = request.args.get('type', 'users')
    days = request.args.get('days', 30, type=int)
    
    if export_type == 'users':
        # Exporter les utilisateurs
        users = User.query.filter_by(role='user').all()
        data = [user.to_dict() for user in users]
        
    elif export_type == 'calculs':
        # Exporter les calculs
        calculs_data = heatmap_service.export_data_json(days=days)
        return jsonify(calculs_data)
        
    elif export_type == 'logs':
        # Exporter les logs de sécurité
        logs = SecurityLog.query.filter(
            SecurityLog.created_at >= datetime.utcnow() - timedelta(days=days)
        ).all()
        data = [log.to_dict() for log in logs]
    
    return jsonify(data)

@admin_bp.route('/system/cleanup', methods=['POST'])
@login_required
@admin_required
def system_cleanup():
    """
    Nettoyage des anciennes données système
    """
    days = request.form.get('days', 90, type=int)
    
    # Nettoyer les anciennes données
    cleanup_stats = security_service.cleanup_old_data(days=days)
    
    flash(f'Nettoyage effectué : {cleanup_stats["deleted_security_logs"]} logs et {cleanup_stats["deleted_ddos_records"]} enregistrements DDoS supprimés.', 'info')
    
    return redirect(url_for('admin.dashboard'))

# API routes pour l'admin
@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """
    API pour les statistiques en temps réel
    """
    admin = Admin.query.get(current_user.id)
    stats = admin.get_statistics()
    
    # Ajouter les statistiques récentes
    stats['recent_anomalies'] = security_service.detect_anomalies(hours=1)
    stats['active_users_24h'] = User.query.filter(
        User.last_login >= datetime.utcnow() - timedelta(hours=24)
    ).count() if hasattr(User, 'last_login') else 0
    
    return jsonify(stats)

@admin_bp.route('/api/heatmap-data')
@login_required
@admin_required
def api_heatmap_data():
    """
    API pour les données de heatmap
    """
    days = request.args.get('days', 30, type=int)
    admin = Admin.query.get(current_user.id)
    
    heatmap_data = admin.get_heatmap_data(days=days)
    return jsonify(heatmap_data)
