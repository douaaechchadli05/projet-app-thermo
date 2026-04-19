import sys
import traceback
from app_complete import app

def test_routes():
    """Test toutes les routes pour identifier les erreurs"""
    print("=== TEST DES ROUTES ===\n")
    
    with app.test_client() as client:
        routes_to_test = [
            '/',
            '/login',
            '/register',
            '/calcul',
            '/historique',
            '/admin'
        ]
        
        for route in routes_to_test:
            try:
                print(f"Test {route}...")
                response = client.get(route)
                print(f"  Status: {response.status_code}")
                if response.status_code >= 400:
                    print(f"  Error: {response.data.decode()[:500]}")
                else:
                    print(f"  OK")
            except Exception as e:
                print(f"  Exception: {e}")
                print(f"  Traceback: {traceback.format_exc()}")
            print()

def check_templates():
    """Vérifie que tous les templates existent"""
    print("=== VÉRIFICATION DES TEMPLATES ===\n")
    
    import os
    templates = [
        'templates/index_modern.html',
        'templates/login.html',
        'templates/register.html',
        'templates/calcul_moderne.html',
        'templates/historique_modern.html',
        'templates/admin_dashboard.html'
    ]
    
    for template in templates:
        if os.path.exists(template):
            print(f"  {template}: OK")
        else:
            print(f"  {template}: MANQUANT")

def check_database():
    """Vérifie les bases de données"""
    print("=== VÉRIFICATION DES BASES DE DONNÉES ===\n")
    
    import sqlite3
    import os
    
    databases = ['users.db', 'admin.db']
    
    for db in databases:
        if os.path.exists(db):
            try:
                conn = sqlite3.connect(db)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"  {db}: OK (tables: {[t[0] for t in tables]})")
                conn.close()
            except Exception as e:
                print(f"  {db}: ERREUR - {e}")
        else:
            print(f"  {db}: MANQUANTE")

if __name__ == "__main__":
    print("DIAGNOSTIC DE L'APPLICATION\n")
    check_templates()
    check_database()
    test_routes()
