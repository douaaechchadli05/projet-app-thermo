import sqlite3
import os
from tabulate import tabulate

def read_database():
    """Lire et afficher toutes les données des bases de données"""
    
    # Chemins des bases de données
    USERS_DB = os.path.join(os.path.dirname(__file__), 'users.db')
    ADMIN_DB = os.path.join(os.path.dirname(__file__), 'admin.db')
    
    print("=" * 80)
    print("LECTURE DES BASES DE DONNÉES - THERMOCALC")
    print("=" * 80)
    
    # Lire la base de données utilisateurs
    print("\n" + "=" * 40)
    print("BASE DE DONNÉES UTILISATEURS")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        
        # Afficher les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables trouvées: {[table[0] for table in tables]}")
        
        # Lire les utilisateurs
        print("\n--- UTILISATEURS ---")
        cursor.execute("SELECT id, username, email, created_at, is_active FROM users")
        users = cursor.fetchall()
        
        if users:
            headers = ["ID", "Username", "Email", "Created_at", "Active"]
            print(tabulate(users, headers=headers, tablefmt="grid"))
        else:
            print("Aucun utilisateur trouvé")
        
        # Lire les calculs
        print("\n--- CALCULS DES UTILISATEURS ---")
        cursor.execute("""
            SELECT id, user_id, nom, date, temperature, x1, x2, p_bulle, y1, y2 
            FROM user_calculations 
            ORDER BY id DESC 
            LIMIT 10
        """)
        calculations = cursor.fetchall()
        
        if calculations:
            headers = ["ID", "User_ID", "Nom", "Date", "Temp", "x1", "x2", "P_bulle", "y1", "y2"]
            print(tabulate(calculations, headers=headers, tablefmt="grid"))
        else:
            print("Aucun calcul trouvé")
        
        # Lire les sessions (si la table existe)
        print("\n--- SESSIONS UTILISATEURS ---")
        try:
            cursor.execute("""
                SELECT user_id, username, action, login_time, logout_time 
                FROM user_sessions 
                ORDER BY login_time DESC 
                LIMIT 10
            """)
            sessions = cursor.fetchall()
            
            if sessions:
                headers = ["User_ID", "Username", "Action", "Login_time", "Logout_time"]
                print(tabulate(sessions, headers=headers, tablefmt="grid"))
            else:
                print("Aucune session trouvée")
        except sqlite3.OperationalError:
            print("Table user_sessions non trouvée")
            
        conn.close()
        
    except Exception as e:
        print(f"Erreur lecture base utilisateurs: {e}")
    
    # Lire la base de données admin
    print("\n" + "=" * 40)
    print("BASE DE DONNÉES ADMIN")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(ADMIN_DB)
        cursor = conn.cursor()
        
        # Afficher les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables trouvées: {[table[0] for table in tables]}")
        
        # Lire les activités
        print("\n--- ACTIVITÉS UTILISATEURS ---")
        try:
            # Vérifier d'abord la structure de la table
            cursor.execute("PRAGMA table_info(user_activities)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'action_type' in columns:
                cursor.execute("""
                    SELECT user_id, username, action_type, details, timestamp 
                    FROM user_activities 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """)
                headers = ["User_ID", "Username", "Action", "Details", "Timestamp"]
            else:
                cursor.execute("""
                    SELECT user_id, username, action, details, timestamp 
                    FROM user_activities 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """)
                headers = ["User_ID", "Username", "Action", "Details", "Timestamp"]
            
            activities = cursor.fetchall()
            
            if activities:
                print(tabulate(activities, headers=headers, tablefmt="grid"))
            else:
                print("Aucune activité trouvée")
        except sqlite3.OperationalError:
            print("Table user_activities non trouvée")
            
        conn.close()
        
    except Exception as e:
        print(f"Erreur lecture base admin: {e}")
    
    # Statistiques
    print("\n" + "=" * 40)
    print("STATISTIQUES")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        
        # Nombre d'utilisateurs
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"Nombre total d'utilisateurs: {user_count}")
        
        # Nombre de calculs
        cursor.execute("SELECT COUNT(*) FROM user_calculations")
        calc_count = cursor.fetchone()[0]
        print(f"Nombre total de calculs: {calc_count}")
        
        # Nombre de sessions
        try:
            cursor.execute("SELECT COUNT(*) FROM user_sessions")
            session_count = cursor.fetchone()[0]
            print(f"Nombre total de sessions: {session_count}")
        except sqlite3.OperationalError:
            print("Table user_sessions non trouvée")
        
        # Dernière activité
        try:
            cursor.execute("SELECT username, timestamp FROM user_sessions ORDER BY timestamp DESC LIMIT 1")
            last_activity = cursor.fetchone()
            if last_activity:
                print(f"Dernière activité: {last_activity[0]} à {last_activity[1]}")
        except sqlite3.OperationalError:
            print("Impossible de récupérer la dernière activité")
        
        conn.close()
        
    except Exception as e:
        print(f"Erreur statistiques: {e}")
    
    print("\n" + "=" * 80)
    print("FIN DE LA LECTURE")
    print("=" * 80)

if __name__ == "__main__":
    read_database()
