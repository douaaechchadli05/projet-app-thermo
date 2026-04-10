#!/usr/bin/env python
# init_db.py - Script d'initialisation de la base de données

from app import app, db
from models import Utilisateur, LogsAuth, HistoriqueCalculs, PressionSaturante
from werkzeug.security import generate_password_hash
import os

def init_database():
    """Crée toutes les tables et un utilisateur admin par défaut"""
    
    with app.app_context():
        # Créer toutes les tables
        print("🔄 Création des tables...")
        db.create_all()
        print("✅ Tables créées avec succès!")
        
        # Vérifier si un admin existe déjà
        admin = Utilisateur.query.filter_by(username='admin').first()
        if not admin:
            print("➕ Création de l'utilisateur admin par défaut...")
            admin = Utilisateur(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin créé:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   ⚠️ CHANGEZ CE MOT DE PASSE EN PRODUCTION!")
        else:
            print("✅ Admin existe déjà")
        
        # Ajouter des données d'exemple pour les pressions saturantes
        print("➕ Vérification des données de pression saturante...")
        if PressionSaturante.query.count() == 0:
            print("   Ajout des constantes d'Antoine...")
            # Données d'exemple (loi d'Antoine: log10(P) = A - B/(C+T))
            # Ces données sont les constantes utilisées par effectuer_calcul
            db.session.add(PressionSaturante(composant='benzene', temperature=20, pression=10.13))
            db.session.add(PressionSaturante(composant='benzene', temperature=50, pression=40.65))
            db.session.add(PressionSaturante(composant='benzene', temperature=80, pression=130.5))
            db.session.add(PressionSaturante(composant='toluene', temperature=20, pression=2.92))
            db.session.add(PressionSaturante(composant='toluene', temperature=50, pression=13.78))
            db.session.add(PressionSaturante(composant='toluene', temperature=80, pression=58.5))
            db.session.commit()
            print("✅ Données de pression saturante ajoutées")
        else:
            print("✅ Données existantes")
        
        print("\n" + "="*50)
        print("✨ Base de données initialisée avec succès!")
        print("="*50)
        db_path = os.path.join(os.path.dirname(__file__), 'thermo_app.db')
        print(f"\n📁 Fichier DB: {db_path}")
        print(f"\n🔑 Credentials par défaut:")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"\n⚠️  À FAIRE:")
        print(f"   1. Changer le mot de passe admin")
        print(f"   2. Configurer MAIL_* dans .env")
        print(f"   3. Lancer: python app.py")

if __name__ == '__main__':
    init_database()
