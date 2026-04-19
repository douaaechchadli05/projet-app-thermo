"""
Service Mail pour l'envoi d'emails de vérification et notifications
Utilise Flask-Mail avec SMTP Gmail pour la vérification email
"""

from flask import current_app, render_template
from flask_mail import Message, Mail
from itsdangerous import URLSafeTimedSerializer
import os

class MailService:
    """
    Service centralisé pour l'envoi d'emails
    Gère la vérification email, les notifications et les emails de réinitialisation
    """
    
    def __init__(self):
        """Initialise le service mail"""
        self.mail = Mail()
    
    def send_verification_email(self, user):
        """
        Envoie un email de vérification à un nouvel utilisateur
        
        Args:
            user: Objet User avec email et token de vérification
        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        try:
            # Générer le token s'il n'existe pas
            if not user.verify_token:
                user.generate_verify_token()
            
            # Créer le message
            msg = Message(
                subject='Vérifiez votre email - Calculateur Loi de Raoult',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email]
            )
            
            # Corps de l'email en HTML
            msg.html = render_template(
                'emails/verification_email.html',
                user=user,
                verification_url=f"{self._get_base_url()}/auth/verify/{user.verify_token}"
            )
            
            # Envoyer l'email
            self.mail.send(msg)
            return True
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'envoi de l'email de vérification: {e}")
            return False
    
    def send_welcome_email(self, user):
        """
        Envoie un email de bienvenue après vérification
        
        Args:
            user: Objet User vérifié
        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        try:
            msg = Message(
                subject='Bienvenue sur le Calculateur Loi de Raoult !',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email]
            )
            
            msg.html = render_template(
                'emails/welcome_email.html',
                user=user,
                login_url=f"{self._get_base_url()}/auth/login"
            )
            
            self.mail.send(msg)
            return True
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {e}")
            return False
    
    def send_password_reset_email(self, user, reset_token):
        """
        Envoie un email de réinitialisation de mot de passe
        
        Args:
            user: Objet User
            reset_token: Token de réinitialisation
        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        try:
            msg = Message(
                subject='Réinitialisation de votre mot de passe',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email]
            )
            
            msg.html = render_template(
                'emails/password_reset_email.html',
                user=user,
                reset_url=f"{self._get_base_url()}/auth/reset-password/{reset_token}",
                expiry_hours=24
            )
            
            self.mail.send(msg)
            return True
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation: {e}")
            return False
    
    def send_admin_notification(self, subject, message, recipients=None):
        """
        Envoie une notification aux administrateurs
        
        Args:
            subject (str): Sujet de la notification
            message (str): Message à envoyer
            recipients (list): Liste des emails des admins (optionnel)
        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        try:
            # Récupérer les emails des administrateurs si non spécifiés
            if not recipients:
                from models.user import User
                admins = User.query.filter_by(role='admin').all()
                recipients = [admin.email for admin in admins]
            
            if not recipients:
                return False
            
            msg = Message(
                subject=f'[ADMIN] {subject}',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=recipients
            )
            
            msg.html = render_template(
                'emails/admin_notification.html',
                subject=subject,
                message=message,
                timestamp=datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')
            )
            
            self.mail.send(msg)
            return True
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'envoi de la notification admin: {e}")
            return False
    
    def send_suspicious_activity_alert(self, ip_address, attempts_count, user_agent=None):
        """
        Envoie une alerte pour activité suspecte
        
        Args:
            ip_address (str): Adresse IP suspecte
            attempts_count (int): Nombre de tentatives
            user_agent (str): User agent de la tentative
        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        try:
            from models.user import User
            admins = User.query.filter_by(role='admin').all()
            recipients = [admin.email for admin in admins]
            
            if not recipients:
                return False
            
            msg = Message(
                subject='Alerte Activité Suspecte',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=recipients
            )
            
            msg.html = render_template(
                'emails/suspicious_activity_alert.html',
                ip_address=ip_address,
                attempts_count=attempts_count,
                user_agent=user_agent,
                timestamp=datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')
            )
            
            self.mail.send(msg)
            return True
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'envoi de l'alerte suspecte: {e}")
            return False
    
    def generate_reset_token(self, user):
        """
        Génère un token de réinitialisation de mot de passe
        
        Args:
            user: Objet User
        Returns:
            str: Token de réinitialisation
        """
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(
            {'user_id': user.id, 'email': user.email},
            salt='password-reset'
        )
    
    def verify_reset_token(self, token, max_age=86400):
        """
        Vérifie un token de réinitialisation
        
        Args:
            token (str): Token à vérifier
            max_age (int): Durée de validité en secondes (défaut: 24h)
        Returns:
            dict: Données utilisateur ou None si invalide
        """
        try:
            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            data = serializer.loads(
                token,
                salt='password-reset',
                max_age=max_age
            )
            return data
        except:
            return None
    
    def _get_base_url(self):
        """
        Détermine l'URL de base de l'application
        
        Returns:
            str: URL de base
        """
        # En production, vous pourriez utiliser une variable d'environnement
        # Pour le développement, on utilise localhost
        return os.getenv('BASE_URL', 'http://localhost:5000')
    
    def test_email_configuration(self):
        """
        Teste la configuration email
        
        Returns:
            dict: Résultat du test
        """
        try:
            msg = Message(
                subject='Test de configuration email',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[current_app.config['MAIL_DEFAULT_SENDER']]
            )
            msg.body = 'Ceci est un test de configuration email.'
            
            self.mail.send(msg)
            return {'success': True, 'message': 'Email de test envoyé avec succès'}
            
        except Exception as e:
            return {'success': False, 'message': f'Erreur: {str(e)}'}

# Instance globale du service mail
mail_service = MailService()
