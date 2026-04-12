import sqlite3
import os
from app_complete import app, USERS_DB, ADMIN_DB

def test_database_connections():
    """Teste toutes les connexions aux bases de données"""
    print("=== TEST DES CONNEXIONS BASES DE DONNÉES ===\n")
    
    # Test base users.db
    try:
        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        
        # Vérifier les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"users.db - Tables: {[t[0] for t in tables]}")
        
        # Vérifier les données users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"users.db - Utilisateurs: {user_count}")
        
        # Vérifier les données calculs
        cursor.execute("SELECT COUNT(*) FROM user_calculations")
        calc_count = cursor.fetchone()[0]
        print(f"users.db - Calculs: {calc_count}")
        
        conn.close()
        print("users.db: CONNEXION OK")
        
    except Exception as e:
        print(f"users.db: ERREUR - {e}")
    
    print()
    
    # Test base admin.db
    try:
        conn = sqlite3.connect(ADMIN_DB)
        cursor = conn.cursor()
        
        # Vérifier les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"admin.db - Tables: {[t[0] for t in tables]}")
        
        # Vérifier les données sessions
        cursor.execute("SELECT COUNT(*) FROM user_sessions")
        session_count = cursor.fetchone()[0]
        print(f"admin.db - Sessions: {session_count}")
        
        # Vérifier les données activités
        cursor.execute("SELECT COUNT(*) FROM user_activities")
        activity_count = cursor.fetchone()[0]
        print(f"admin.db - Activités: {activity_count}")
        
        # Vérifier les données heatmap
        cursor.execute("SELECT COUNT(*) FROM heatmap_data")
        heatmap_count = cursor.fetchone()[0]
        print(f"admin.db - Heatmap: {heatmap_count}")
        
        conn.close()
        print("admin.db: CONNEXION OK")
        
    except Exception as e:
        print(f"admin.db: ERREUR - {e}")

def test_flask_login_integration():
    """Teste l'intégration Flask-Login"""
    print("\n=== TEST INTEGRATION FLASK-LOGIN ===\n")
    
    try:
        from app_complete import User, login_manager, load_user
        
        # Test création utilisateur
        test_user = User(1, "testuser", "test@example.com")
        print(f"User créé: {test_user.username} (ID: {test_user.id})")
        
        # Test user_loader (simulé)
        print("User loader configuré:", login_manager is not None)
        print("Login view:", login_manager.login_view)
        
        print("Flask-Login: INTÉGRATION OK")
        
    except Exception as e:
        print(f"Flask-Login: ERREUR - {e}")

def test_template_routes():
    """Teste les routes et templates"""
    print("\n=== TEST ROUTES ET TEMPLATES ===\n")
    
    routes_to_test = [
        ('/', 'index_modern.html'),
        ('/login', 'login.html'),
        ('/register', 'register.html'),
        ('/calcul', 'calcul_moderne.html'),
        ('/historique', 'historique_modern.html'),
        ('/admin', 'admin_dashboard.html')
    ]
    
    with app.test_client() as client:
        for route, template in routes_to_test:
            try:
                response = client.get(route)
                if response.status_code in [200, 302]:  # 200 OK ou 302 redirection
                    print(f"{route} -> {template}: ROUTE OK ({response.status_code})")
                else:
                    print(f"{route} -> {template}: ERREUR ({response.status_code})")
            except Exception as e:
                print(f"{route} -> {template}: ERREUR - {e}")

def test_template_links():
    """Teste les liens dans les templates"""
    print("\n=== TEST LIENS TEMPLATES ===\n")
    
    template_files = [
        'templates/index_modern.html',
        'templates/login.html',
        'templates/register.html',
        'templates/calcul_moderne.html',
        'templates/historique_modern.html',
        'templates/admin_dashboard.html'
    ]
    
    for template_file in template_files:
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Rechercher les liens Flask
            import re
            flask_links = re.findall(r'href=[\'"](\/[^\'"]*)[\'"]', content)
            flask_forms = re.findall(r'action=[\'"](\/[^\'"]*)[\'"]', content)
            
            print(f"{template_file}:")
            print(f"  Liens trouvés: {len(flask_links)}")
            for link in flask_links[:5]:  # Limiter l'affichage
                print(f"    {link}")
            if len(flask_links) > 5:
                print(f"    ... et {len(flask_links) - 5} autres")
                
            print(f"  Forms trouvés: {len(flask_forms)}")
            for form in flask_forms:
                print(f"    {form}")
            print()
        else:
            print(f"{template_file}: FICHIER MANQUANT")

def test_session_tracking():
    """Teste le tracking des sessions"""
    print("\n=== TEST TRACKING SESSIONS ===\n")
    
    try:
        from app_complete import log_user_session, log_user_activity, get_client_info
        
        # Test des fonctions de tracking
        print("Fonctions de tracking disponibles:")
        print("  - log_user_session:", callable(log_user_session))
        print("  - log_user_activity:", callable(log_user_activity))
        print("  - get_client_info:", callable(get_client_info))
        
        print("Session tracking: CONFIGURATION OK")
        
    except Exception as e:
        print(f"Session tracking: ERREUR - {e}")

if __name__ == "__main__":
    test_database_connections()
    test_flask_login_integration()
    test_template_routes()
    test_template_links()
    test_session_tracking()
    
    print("\n=== RÉCAPITULATIF ===")
    print("Vérifiez les messages ci-dessus pour identifier les problèmes.")
