"""
Service Security pour la gestion de la sécurité et la géolocalisation
Gère les tentatives DDoS, la géolocalisation IP et le logging de sécurité
"""

import requests
import socket
from datetime import datetime, timedelta
from flask import request, current_app
from models.security_log import SecurityLog
from models.ddos_attempts import DDOSAttempts

class SecurityService:
    """
    Service centralisé pour la gestion de la sécurité
    Géolocalisation, anti-DDoS, logging et surveillance
    """
    
    def __init__(self):
        """Initialise le service de sécurité"""
        self.ip_api_url = "http://ip-api.com/json/"
        self.timeout = 5  # Timeout en secondes pour les API externes
    
    def get_client_ip(self):
        """
        Récupère l'adresse IP réelle du client
        
        Returns:
            str: Adresse IP du client
        """
        # Vérifier les headers pour les proxys
        if request.headers.getlist("X-Forwarded-For"):
            return request.headers.getlist("X-Forwarded-For")[0]
        elif request.headers.get("X-Real-IP"):
            return request.headers.get("X-Real-IP")
        else:
            return request.remote_addr
    
    def get_user_agent(self):
        """
        Récupère le user agent du client
        
        Returns:
            str: User agent ou None
        """
        return request.headers.get('User-Agent')
    
    def geolocate_ip(self, ip_address):
        """
        Géolocalise une adresse IP via ip-api.com
        
        Args:
            ip_address (str): Adresse IP à géolocaliser
        Returns:
            dict: Données de géolocalisation ou None
        """
        try:
            # Ne pas géolocaliser les adresses locales
            if self._is_private_ip(ip_address):
                return {
                    'country': 'Local',
                    'city': 'Local Network',
                    'latitude': 0.0,
                    'longitude': 0.0
                }
            
            # Appel à l'API ip-api.com
            response = requests.get(
                f"{self.ip_api_url}{ip_address}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'latitude': data.get('lat', 0.0),
                        'longitude': data.get('lon', 0.0),
                        'isp': data.get('isp', 'Unknown'),
                        'org': data.get('org', 'Unknown')
                    }
            
        except requests.RequestException as e:
            current_app.logger.warning(f"Erreur de géolocalisation pour {ip_address}: {e}")
        except Exception as e:
            current_app.logger.error(f"Erreur inattendue lors de la géolocalisation: {e}")
        
        return None
    
    def _is_private_ip(self, ip_address):
        """
        Vérifie si une IP est privée/locale
        
        Args:
            ip_address (str): Adresse IP à vérifier
        Returns:
            bool: True si l'IP est privée
        """
        try:
            # Adresses spéciales
            if ip_address in ['127.0.0.1', '::1', 'localhost']:
                return True
            
            # Plages IP privées IPv4
            private_ranges = [
                '10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.',
                '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
                '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.'
            ]
            
            for range_prefix in private_ranges:
                if ip_address.startswith(range_prefix):
                    return True
            
            return False
            
        except:
            return True  # En cas d'erreur, considérer comme privée par sécurité
    
    def check_ddos_protection(self, ip_address):
        """
        Vérifie la protection DDoS et enregistre les tentatives
        
        Args:
            ip_address (str): Adresse IP à vérifier
        Returns:
            dict: Résultat de la vérification DDoS
        """
        # Vérifier si l'IP est déjà bloquée
        if DDOSAttempts.is_blocked(ip_address):
            return {
                'blocked': True,
                'message': 'IP temporairement bloquée pour raisons de sécurité'
            }
        
        # Enregistrer la tentative et vérifier si on doit bloquer
        result = DDOSAttempts.record_attempt(ip_address)
        
        # Envoyer une alerte si l'IP est bloquée
        if result['blocked']:
            from services.mail_service import mail_service
            mail_service.send_suspicious_activity_alert(
                ip_address=ip_address,
                attempts_count=result['attempts'],
                user_agent=self.get_user_agent()
            )
        
        return result
    
    def log_security_event(self, action, user_id=None, geo_data=None):
        """
        Enregistre un événement de sécurité
        
        Args:
            action (str): Type d'action (login, logout, failed_login, etc.)
            user_id (int, optional): ID de l'utilisateur
            geo_data (dict, optional): Données de géolocalisation
        Returns:
            SecurityLog: Log créé
        """
        ip_address = self.get_client_ip()
        user_agent = self.get_user_agent()
        
        # Récupérer les données de géolocalisation si non fournies
        if not geo_data:
            geo_data = self.geolocate_ip(ip_address)
        
        # Créer le log approprié selon l'action
        if action == 'login':
            return SecurityLog.log_login(user_id, ip_address, user_agent, geo_data)
        elif action == 'logout':
            return SecurityLog.log_logout(user_id, ip_address, user_agent)
        elif action == 'failed_login':
            return SecurityLog.log_failed_login(ip_address, user_agent)
        elif action == 'register':
            return SecurityLog.log_registration(user_id, ip_address, user_agent, geo_data)
        else:
            return SecurityLog.log_suspicious_activity(ip_address, user_agent, action, user_id)
    
    def validate_request(self, max_attempts_per_minute=5):
        """
        Valide une requête entrante contre les attaques
        
        Args:
            max_attempts_per_minute (int): Limite de tentatives par minute
        Returns:
            tuple: (bool valide, str message_erreur)
        """
        ip_address = self.get_client_ip()
        
        # Vérifier la protection DDoS
        ddos_result = self.check_ddos_protection(ip_address)
        if ddos_result['blocked']:
            return False, ddos_result['message']
        
        # Vérifier le nombre de tentatives récentes
        recent_attempts = SecurityLog.get_ip_attempts(ip_address, minutes=1)
        if recent_attempts >= max_attempts_per_minute:
            return False, "Trop de tentatives. Veuillez patienter une minute."
        
        return True, ""
    
    def get_connection_statistics(self, days=30):
        """
        Récupère des statistiques sur les connexions
        
        Args:
            days (int): Nombre de jours à analyser
        Returns:
            dict: Statistiques de connexion
        """
        from sqlalchemy import func
        from models.security_log import SecurityLog
        
        since = datetime.utcnow() - timedelta(days=days)
        
        # Statistiques générales
        total_connections = SecurityLog.query.filter(
            SecurityLog.action == 'login',
            SecurityLog.created_at >= since
        ).count()
        
        # Connexions par pays
        connections_by_country = db.session.query(
            SecurityLog.country,
            func.count(SecurityLog.id).label('count')
        ).filter(
            SecurityLog.action == 'login',
            SecurityLog.created_at >= since,
            SecurityLog.country.isnot(None)
        ).group_by(
            SecurityLog.country
        ).order_by(
            func.count(SecurityLog.id).desc()
        ).limit(10).all()
        
        # Connexions uniques par jour
        daily_connections = db.session.query(
            func.date(SecurityLog.created_at).label('date'),
            func.count(func.distinct(SecurityLog.ip_address)).label('unique_ips')
        ).filter(
            SecurityLog.action == 'login',
            SecurityLog.created_at >= since
        ).group_by(
            func.date(SecurityLog.created_at)
        ).order_by('date').all()
        
        return {
            'total_connections': total_connections,
            'connections_by_country': [
                {'country': c.country, 'count': c.count} 
                for c in connections_by_country
            ],
            'daily_connections': [
                {'date': str(d.date), 'unique_ips': d.unique_ips}
                for d in daily_connections
            ]
        }
    
    def detect_anomalies(self, hours=24):
        """
        Détecte des anomalies dans les logs de sécurité
        
        Args:
            hours (int): Période d'analyse en heures
        Returns:
            list: Liste des anomalies détectées
        """
        anomalies = []
        
        # IP suspectes avec beaucoup de tentatives
        suspicious_ips = SecurityLog.get_suspicious_ips(hours=hours, threshold=10)
        if suspicious_ips:
            anomalies.append({
                'type': 'suspicious_ips',
                'message': f"{len(suspicious_ips)} IP(s) suspecte(s) détectée(s)",
                'data': suspicious_ips
            })
        
        # Tentatives DDoS
        ddos_stats = DDOSAttempts.get_statistics()
        if ddos_stats['blocked_ips'] > 0:
            anomalies.append({
                'type': 'ddos_blocked',
                'message': f"{ddos_stats['blocked_ips']} IP(s) bloquée(s) pour DDoS",
                'data': ddos_stats
            })
        
        # Pics de connexions inhabituels
        recent_connections = self.get_connection_statistics(days=1)
        if recent_connections['total_connections'] > 1000:  # Seuil arbitraire
            anomalies.append({
                'type': 'connection_spike',
                'message': f"Pic de connexions détecté: {recent_connections['total_connections']} connexions en 24h",
                'data': recent_connections
            })
        
        return anomalies
    
    def cleanup_old_data(self, days=90):
        """
        Nettoie les anciennes données de sécurité
        
        Args:
            days (int): Âge maximum des données à conserver
        Returns:
            dict: Statistiques du nettoyage
        """
        # Nettoyer les anciens logs de sécurité
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_logs = SecurityLog.query.filter(
            SecurityLog.created_at < cutoff_date
        ).delete()
        
        # Nettoyer les anciennes tentatives DDoS
        deleted_ddos = DDOSAttempts.cleanup_old_records(days=days)
        
        from app_complete import db
        db.session.commit()
        
        return {
            'deleted_security_logs': deleted_logs,
            'deleted_ddos_records': deleted_ddos,
            'cleanup_date': datetime.utcnow().isoformat()
        }

# Instance globale du service de sécurité
security_service = SecurityService()
