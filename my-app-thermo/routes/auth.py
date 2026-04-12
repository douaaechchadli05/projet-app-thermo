"""
Routes d'authentification pour l'application Flask
Gère l'inscription, connexion, déconnexion et vérification email
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models.user import User
from services.mail_service import mail_service
from services.security_service import security_service

# Création du blueprint pour les routes d'authentification
auth_bp = Blueprint('auth', __name__)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["5 per minute"]
)

# Formulaires WTForms
class RegistrationForm(FlaskForm):
    """Formulaire d'inscription"""
    username = StringField('Nom d\'utilisateur', 
                          validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', 
                       validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', 
                            validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField('Confirmer le mot de passe', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('S\'inscrire')
    
    def validate_username(self, username):
        """Vérifie que le nom d'utilisateur n'existe pas déjà"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ce nom d\'utilisateur est déjà pris.')
    
    def validate_email(self, email):
        """Vérifie que l'email n'existe pas déjà"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cet email est déjà utilisé.')

class LoginForm(FlaskForm):
    """Formulaire de connexion"""
    username = StringField('Nom d\'utilisateur ou Email', 
                         validators=[DataRequired()])
    password = PasswordField('Mot de passe', 
                            validators=[DataRequired()])
    submit = SubmitField('Se connecter')

class ForgotPasswordForm(FlaskForm):
    """Formulaire de mot de passe oublié"""
    email = StringField('Email', 
                       validators=[DataRequired(), Email()])
    submit = SubmitField('Envoyer le lien de réinitialisation')

class ResetPasswordForm(FlaskForm):
    """Formulaire de réinitialisation de mot de passe"""
    password = PasswordField('Nouveau mot de passe', 
                            validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField('Confirmer le mot de passe', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Réinitialiser le mot de passe')

# Routes
@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    """
    Route d'inscription des nouveaux utilisateurs
    """
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Validation de la requête
        is_valid, error_message = security_service.validate_request()
        if not is_valid:
            flash(error_message, 'danger')
            return render_template('auth/register.html', form=form)
        
        try:
            # Créer le nouvel utilisateur
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            
            # Sauvegarder dans la base de données
            from app_complete import db
            db.session.add(user)
            db.session.commit()
            
            # Envoyer l'email de vérification
            if mail_service.send_verification_email(user):
                flash('Un email de vérification a été envoyé à votre adresse email.', 'success')
            else:
                flash('L\'email de vérification n\'a pas pu être envoyé. Contactez l\'administrateur.', 'warning')
            
            # Logger l'inscription
            security_service.log_security_event('register', user.id)
            
            # Rediriger vers la page de connexion
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'inscription: {e}")
            flash('Une erreur est survenue lors de l\'inscription. Veuillez réessayer.', 'danger')
            from app_complete import db
            db.session.rollback()
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """
    Route de connexion des utilisateurs
    """
    # Rediriger si déjà connecté
    if current_user.is_authenticated:
        return redirect(url_for('calcul.calcul_page'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Validation de la requête
        is_valid, error_message = security_service.validate_request()
        if not is_valid:
            flash(error_message, 'danger')
            return render_template('auth/login.html', form=form)
        
        username_or_email = form.username.data
        password = form.password.data
        
        # Rechercher l'utilisateur par nom ou email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            # Vérifier si l'email est vérifié
            if not user.is_verified:
                flash('Veuillez vérifier votre email avant de vous connecter.', 'warning')
                return render_template('auth/login.html', form=form)
            
            # Connexion réussie
            login_user(user, remember=True)
            
            # Logger la connexion
            security_service.log_security_event('login', user.id)
            
            # Redirection selon le rôle
            next_page = request.args.get('next')
            if user.is_admin():
                return redirect(next_page or url_for('admin.dashboard'))
            else:
                return redirect(next_page or url_for('calcul.calcul_page'))
        else:
            # Échec de connexion
            security_service.log_security_event('failed_login')
            flash('Nom d\'utilisateur/email ou mot de passe incorrect.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """
    Route de déconnexion
    """
    # Logger la déconnexion
    security_service.log_security_event('logout', current_user.id)
    
    logout_user()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/verify/<token>')
def verify_email(token):
    """
    Route de vérification d'email via token
    """
    try:
        # Rechercher l'utilisateur avec ce token
        user = User.query.filter_by(verify_token=token).first()
        
        if user and user.verify_email_token(token):
            # Confirmer l'email
            user.confirm_email()
            
            # Envoyer l'email de bienvenue
            mail_service.send_welcome_email(user)
            
            flash('Votre email a été vérifié avec succès ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Le lien de vérification est invalide ou a expiré.', 'danger')
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la vérification email: {e}")
        flash('Une erreur est survenue lors de la vérification.', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
@limiter.limit("2 per minute")
def resend_verification():
    """
    Route pour renvoyer l'email de vérification
    """
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and not user.is_verified:
            # Régénérer le token et envoyer l'email
            user.generate_verify_token()
            if mail_service.send_verification_email(user):
                flash('Un nouvel email de vérification a été envoyé.', 'success')
            else:
                flash('Erreur lors de l\'envoi de l\'email. Veuillez réessayer plus tard.', 'danger')
        elif user and user.is_verified:
            flash('Cet email est déjà vérifié.', 'info')
        else:
            flash('Aucun utilisateur trouvé avec cet email.', 'warning')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/resend_verification.html', form=form)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def forgot_password():
    """
    Route pour la demande de réinitialisation de mot de passe
    """
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            # Générer le token de réinitialisation
            reset_token = mail_service.generate_reset_token(user)
            
            # Envoyer l'email de réinitialisation
            if mail_service.send_password_reset_email(user, reset_token):
                flash('Un email de réinitialisation a été envoyé à votre adresse.', 'success')
            else:
                flash('Erreur lors de l\'envoi de l\'email. Veuillez réessayer plus tard.', 'danger')
        else:
            # Ne pas révéler si l'email existe ou pas (sécurité)
            flash('Si cet email existe dans notre base de données, un lien de réinitialisation a été envoyé.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def reset_password(token):
    """
    Route de réinitialisation de mot de passe
    """
    # Vérifier le token
    token_data = mail_service.verify_reset_token(token)
    
    if not token_data:
        flash('Le lien de réinitialisation est invalide ou a expiré.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    # Récupérer l'utilisateur
    user = User.query.get(token_data['user_id'])
    if not user:
        flash('Utilisateur non trouvé.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        # Mettre à jour le mot de passe
        user.set_password(form.password.data)
        from app_complete import db
        db.session.commit()
        
        flash('Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)

@auth_bp.route('/profile')
@login_required
def profile():
    """
    Route du profil utilisateur
    """
    user_stats = User.get_statistics(current_user.id)
    return render_template('auth/profile.html', user_stats=user_stats)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour")
def change_password():
    """
    Route pour changer le mot de passe
    """
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        current_user.set_password(form.password.data)
        from app_complete import db
        db.session.commit()
        
        flash('Votre mot de passe a été changé avec succès.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html', form=form)
