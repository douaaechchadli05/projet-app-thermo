"""
Service Heatmap pour la génération de cartes de chaleur interactives
Utilise Folium pour créer des visualisations géographiques des connexions
"""

import folium
from folium.plugins import HeatMap, MarkerCluster
import json
from datetime import datetime, timedelta
from models.security_log import SecurityLog
from models.user import User
from sqlalchemy import func

class HeatmapService:
    """
    Service pour générer des heatmaps et cartes interactives
    Visualise les connexions utilisateurs par géolocalisation
    """
    
    def __init__(self):
        """Initialise le service heatmap"""
        self.default_center = [48.8566, 2.3522]  # Paris par défaut
        self.default_zoom = 2
    
    def generate_world_heatmap(self, days=30, save_path=None):
        """
        Génère une heatmap mondiale des connexions
        
        Args:
            days (int): Nombre de jours à considérer
            save_path (str, optional): Chemin pour sauvegarder la carte
        Returns:
            str: HTML de la carte ou chemin du fichier sauvegardé
        """
        # Récupérer les données de connexion
        connection_data = self._get_connection_data(days)
        
        if not connection_data:
            return self._generate_empty_map("Aucune donnée de connexion disponible")
        
        # Créer la carte de base
        m = folium.Map(
            location=self.default_center,
            zoom_start=self.default_zoom,
            tiles='OpenStreetMap'
        )
        
        # Ajouter différentes couches de tuiles
        folium.TileLayer('cartodbpositron').add_to(m)
        folium.TileLayer('cartodbdark_matter').add_to(m)
        
        # Préparer les données pour la heatmap
        heat_data = []
        for conn in connection_data:
            if conn['latitude'] and conn['longitude']:
                # Pondérer par le nombre de connexions
                for _ in range(min(conn['connection_count'], 20)):  # Limiter pour éviter la surcharge
                    heat_data.append([conn['latitude'], conn['longitude']])
        
        if heat_data:
            # Ajouter la heatmap
            HeatMap(
                heat_data,
                radius=15,
                blur=10,
                gradient={
                    0.0: 'blue',
                    0.3: 'cyan',
                    0.5: 'lime',
                    0.7: 'yellow',
                    1.0: 'red'
                }
            ).add_to(m)
        
        # Ajouter des marqueurs pour les points chauds
        self._add_cluster_markers(m, connection_data)
        
        # Ajouter les contrôles de couches
        folium.LayerControl().add_to(m)
        
        # Ajouter une légende
        self._add_legend(m)
        
        # Ajouter des statistiques
        stats_html = self._generate_stats_popup(connection_data, days)
        folium.Marker(
            location=self.default_center,
            popup=folium.Popup(stats_html, max_width=300),
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
        
        # Sauvegarder ou retourner le HTML
        if save_path:
            m.save(save_path)
            return save_path
        else:
            return m._repr_html_()
    
    def generate_country_stats_map(self, days=30):
        """
        Génère une carte avec statistiques par pays
        
        Args:
            days (int): Nombre de jours à considérer
        Returns:
            str: HTML de la carte
        """
        # Récupérer les statistiques par pays
        country_stats = self._get_country_statistics(days)
        
        if not country_stats:
            return self._generate_empty_map("Aucune donnée par pays disponible")
        
        # Créer la carte
        m = folium.Map(
            location=self.default_center,
            zoom_start=self.default_zoom,
            tiles='cartodbpositron'
        )
        
        # Ajouter les marqueurs de pays avec statistiques
        for stat in country_stats:
            if stat['latitude'] and stat['longitude']:
                popup_content = f"""
                <b>{stat['country']}</b><br>
                Connexions: {stat['connection_count']}<br>
                Utilisateurs uniques: {stat['unique_users']}<br>
                Ville principale: {stat['main_city']}
                """
                
                folium.CircleMarker(
                    location=[stat['latitude'], stat['longitude']],
                    radius=min(stat['connection_count'] / 10, 30),  # Taille basée sur le nombre de connexions
                    popup=folium.Popup(popup_content, max_width=200),
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.6
                ).add_to(m)
        
        return m._repr_html_()
    
    def generate_user_activity_map(self, user_id, days=30):
        """
        Génère une carte des activités d'un utilisateur spécifique
        
        Args:
            user_id (int): ID de l'utilisateur
            days (int): Nombre de jours à considérer
        Returns:
            str: HTML de la carte
        """
        # Récupérer l'utilisateur
        user = User.query.get(user_id)
        if not user:
            return self._generate_empty_map("Utilisateur non trouvé")
        
        # Récupérer les logs de l'utilisateur
        user_logs = SecurityLog.get_user_activity(user_id, days)
        
        if not user_logs:
            return self._generate_empty_map(f"Aucune activité pour {user.username}")
        
        # Créer la carte
        m = folium.Map(
            location=self.default_center,
            zoom_start=self.default_zoom,
            tiles='OpenStreetMap'
        )
        
        # Grouper les logs par localisation
        locations = {}
        for log in user_logs:
            if log.latitude and log.longitude:
                key = (log.latitude, log.longitude, log.country, log.city)
                if key not in locations:
                    locations[key] = []
                locations[key].append(log)
        
        # Ajouter les marqueurs pour chaque localisation
        for (lat, lon, country, city), logs in locations.items():
            popup_content = f"""
            <b>{user.username}</b><br>
            Pays: {country or 'Inconnu'}<br>
            Ville: {city or 'Inconnue'}<br>
            Connexions: {len(logs)}<br>
            Première: {min(log.created_at for log in logs).strftime('%d/%m/%Y %H:%M')}<br>
            Dernière: {max(log.created_at for log in logs).strftime('%d/%m/%Y %H:%M')}
            """
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=250),
                icon=folium.Icon(color='blue', icon='user')
            ).add_to(m)
        
        # Ajouter une ligne entre les localisations chronologiques
        self._add_activity_path(m, user_logs)
        
        return m._repr_html_()
    
    def _get_connection_data(self, days):
        """
        Récupère les données de connexion pour la heatmap
        
        Args:
            days (int): Nombre de jours
        Returns:
            list: Données de connexion
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Requête pour obtenir les connexions groupées par localisation
        connections = db.session.query(
            SecurityLog.ip_address,
            SecurityLog.country,
            SecurityLog.city,
            SecurityLog.latitude,
            SecurityLog.longitude,
            func.count(SecurityLog.id).label('connection_count'),
            func.count(func.distinct(SecurityLog.user_id)).label('unique_users')
        ).filter(
            SecurityLog.created_at >= start_date,
            SecurityLog.action == 'login',
            SecurityLog.latitude.isnot(None),
            SecurityLog.longitude.isnot(None)
        ).group_by(
            SecurityLog.ip_address,
            SecurityLog.country,
            SecurityLog.city,
            SecurityLog.latitude,
            SecurityLog.longitude
        ).all()
        
        return [{
            'ip_address': conn.ip_address,
            'country': conn.country,
            'city': conn.city,
            'latitude': float(conn.latitude),
            'longitude': float(conn.longitude),
            'connection_count': conn.connection_count,
            'unique_users': conn.unique_users
        } for conn in connections]
    
    def _get_country_statistics(self, days):
        """
        Récupère les statistiques par pays
        
        Args:
            days (int): Nombre de jours
        Returns:
            list: Statistiques par pays
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Coordonnées approximatives des capitales pour le centrage
        country_coordinates = {
            'France': [48.8566, 2.3522],
            'United States': [38.9072, -77.0369],
            'United Kingdom': [51.5074, -0.1278],
            'Germany': [52.5200, 13.4050],
            'Spain': [40.4168, -3.7038],
            'Italy': [41.9028, 12.4964],
            'Canada': [45.4215, -75.6972],
            'Australia': [-35.2809, 149.1300],
            'Japan': [35.6762, 139.6503],
            'China': [39.9042, 116.4074],
            'Brazil': [-15.8267, -47.9218],
            'India': [28.6139, 77.2090],
            'Russia': [55.7558, 37.6173],
            'Mexico': [19.4326, -99.1332],
        }
        
        # Requête pour les statistiques par pays
        stats = db.session.query(
            SecurityLog.country,
            func.count(SecurityLog.id).label('connection_count'),
            func.count(func.distinct(SecurityLog.user_id)).label('unique_users'),
            func.count(func.distinct(SecurityLog.city)).label('cities_count')
        ).filter(
            SecurityLog.created_at >= start_date,
            SecurityLog.action == 'login',
            SecurityLog.country.isnot(None)
        ).group_by(
            SecurityLog.country
        ).order_by(
            func.count(SecurityLog.id).desc()
        ).all()
        
        result = []
        for stat in stats:
            coords = country_coordinates.get(stat.country, [0, 0])
            
            # Récupérer la ville principale
            main_city = db.session.query(
                SecurityLog.city,
                func.count(SecurityLog.id).label('count')
            ).filter(
                SecurityLog.country == stat.country,
                SecurityLog.created_at >= start_date,
                SecurityLog.city.isnot(None)
            ).group_by(
                SecurityLog.city
            ).order_by(
                func.count(SecurityLog.id).desc()
            ).first()
            
            result.append({
                'country': stat.country,
                'connection_count': stat.connection_count,
                'unique_users': stat.unique_users,
                'cities_count': stat.cities_count,
                'main_city': main_city.city if main_city else 'Inconnue',
                'latitude': coords[0],
                'longitude': coords[1]
            })
        
        return result
    
    def _add_cluster_markers(self, map_obj, connection_data):
        """
        Ajoute des marqueurs groupés à la carte
        
        Args:
            map_obj: Objet carte Folium
            connection_data: Données de connexion
        """
        marker_cluster = MarkerCluster().add_to(map_obj)
        
        for conn in connection_data:
            if conn['latitude'] and conn['longitude']:
                popup_content = f"""
                <b>IP: {conn['ip_address']}</b><br>
                Pays: {conn['country'] or 'Inconnu'}<br>
                Ville: {conn['city'] or 'Inconnue'}<br>
                Connexions: {conn['connection_count']}<br>
                Utilisateurs: {conn['unique_users']}
                """
                
                folium.Marker(
                    location=[conn['latitude'], conn['longitude']],
                    popup=folium.Popup(popup_content, max_width=200),
                    icon=folium.Icon(color='red', icon='signal')
                ).add_to(marker_cluster)
    
    def _add_activity_path(self, map_obj, user_logs):
        """
        Ajoute un chemin montrant l'activité chronologique
        
        Args:
            map_obj: Objet carte Folium
            user_logs: Logs de l'utilisateur
        """
        # Filtrer les logs avec coordonnées et trier par date
        locations = []
        for log in sorted(user_logs, key=lambda x: x.created_at):
            if log.latitude and log.longitude:
                locations.append([log.latitude, log.longitude])
        
        # Créer une ligne entre les points
        if len(locations) > 1:
            folium.PolyLine(
                locations=locations,
                color='blue',
                weight=2,
                opacity=0.8,
                dash_array='10, 10'
            ).add_to(map_obj)
    
    def _add_legend(self, map_obj):
        """
        Ajoute une légende à la carte
        
        Args:
            map_obj: Objet carte Folium
        """
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Intensité</b></p>
        <p><i class="fa fa-circle" style="color:blue"></i> Faible</p>
        <p><i class="fa fa-circle" style="color:yellow"></i> Moyenne</p>
        <p><i class="fa fa-circle" style="color:red"></i> Élevée</p>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    def _generate_stats_popup(self, connection_data, days):
        """
        Génère le contenu HTML pour le popup de statistiques
        
        Args:
            connection_data: Données de connexion
            days (int): Nombre de jours
        Returns:
            str: HTML du popup
        """
        total_connections = sum(conn['connection_count'] for conn in connection_data)
        total_users = sum(conn['unique_users'] for conn in connection_data)
        unique_countries = len(set(conn['country'] for conn in connection_data if conn['country']))
        unique_cities = len(set(conn['city'] for conn in connection_data if conn['city']))
        
        return f"""
        <div style="font-family: Arial, sans-serif;">
        <h4>Statistiques des {days} derniers jours</h4>
        <p><b>Connexions totales:</b> {total_connections}</p>
        <p><b>Utilisateurs uniques:</b> {total_users}</p>
        <p><b>Pays:</b> {unique_countries}</p>
        <p><b>Villes:</b> {unique_cities}</p>
        <p><small>Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}</small></p>
        </div>
        """
    
    def _generate_empty_map(self, message):
        """
        Génère une carte vide avec un message
        
        Args:
            message (str): Message à afficher
        Returns:
            str: HTML de la carte vide
        """
        m = folium.Map(
            location=self.default_center,
            zoom_start=self.default_zoom,
            tiles='cartodbpositron'
        )
        
        folium.Marker(
            location=self.default_center,
            popup=message,
            icon=folium.Icon(color='gray', icon='info-sign')
        ).add_to(m)
        
        return m._repr_html_()
    
    def export_data_json(self, days=30, file_path=None):
        """
        Exporte les données de connexion en format JSON
        
        Args:
            days (int): Nombre de jours
            file_path (str, optional): Chemin du fichier de sauvegarde
        Returns:
            str ou dict: Données JSON ou chemin du fichier
        """
        connection_data = self._get_connection_data(days)
        country_stats = self._get_country_statistics(days)
        
        export_data = {
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'days_period': days,
                'total_connections': sum(conn['connection_count'] for conn in connection_data),
                'total_unique_users': sum(conn['unique_users'] for conn in connection_data)
            },
            'connection_data': connection_data,
            'country_statistics': country_stats
        }
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            return file_path
        else:
            return export_data

# Instance globale du service heatmap
heatmap_service = HeatmapService()
