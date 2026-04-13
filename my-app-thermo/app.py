"""
Application Flask - Point d'entrée principal
Importe l'application complète depuis app_complete.py
"""

# Importer l'application complète
from app_complete import app
from app_complete import create_admin, init_db

# Commandes CLI personnalisées
@app.cli.command()
def create_admin():
    """Crée un utilisateur administrateur"""
    from app_complete import create_admin
    create_admin()

@app.cli.command()
def init_db():
    """Initialise la base de données"""
    from app_complete import init_db
    init_db()

if __name__ == '__main__':
    app.run(debug=True)

# Configuration pour le déploiement
import os

# Ne pas initialiser la DB en mode développement
if os.getenv('FLASK_ENV') == 'production':
    # Initialiser les bases de données au déploiement
    init_db()


        