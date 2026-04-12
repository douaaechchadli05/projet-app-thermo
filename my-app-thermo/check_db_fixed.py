import sqlite3
import os

def check_database(db_name):
    """Vérifier une base de données SQLite"""
    print(f"\n=== Vérification de {db_name} ===")
    try:
        # Utiliser le chemin complet
        db_path = os.path.join(os.path.dirname(__file__), db_name)
        print(f"Chemin: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"Le fichier {db_name} n'existe pas")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lister les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables trouvées: {[table[0] for table in tables]}")
        
        # Vérifier les données dans chaque table
        for table in tables:
            table_name = table[0]
            if table_name == 'sqlite_sequence':
                continue  # Ignorer la table système
                
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} enregistrements")
            
            # Afficher quelques exemples pour les tables principales
            if count > 0 and table_name in ['users', 'user_calculations', 'user_sessions', 'user_activities']:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                
                # Obtenir les noms des colonnes
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                
                print(f"    Colonnes: {columns}")
                print(f"    Exemples: {rows}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur: {e}")
        return False

if __name__ == "__main__":
    print("Vérification des bases de données ThermoCalc")
    print("=" * 50)
    
    # Vérifier les deux bases de données
    check_database("users.db")
    check_database("admin.db")
    
    print("\n" + "=" * 50)
    print("Vérification terminée")
