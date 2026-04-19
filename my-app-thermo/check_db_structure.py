import sqlite3
import os

# Chemin vers la base de données
USERS_DB = os.path.join(os.path.dirname(__file__), 'users.db')

def check_users_table():
    """Vérifier la structure de la table users"""
    try:
        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        
        # Obtenir la structure de la table
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("Structure de la table users:")
        for col in columns:
            print(f"  {col}")
        
        # Vérifier si la colonne is_active existe
        has_is_active = any(col[1] == 'is_active' for col in columns)
        print(f"\nColonne 'is_active' présente: {has_is_active}")
        
        # Afficher quelques exemples de données
        cursor.execute("SELECT id, username, is_active FROM users LIMIT 5")
        users = cursor.fetchall()
        
        print(f"\nExemples d'utilisateurs ({len(users)} trouvés):")
        for user in users:
            print(f"  ID: {user[0]}, Username: {user[1]}, Active: {user[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    check_users_table()
