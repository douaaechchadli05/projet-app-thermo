import sqlite3
import os

def check_database(db_name):
    """Vérifier une base de données SQLite"""
    print(f"\n=== Vérification de {db_name} ===")
    try:
        db_path = os.path.join(os.path.dirname(__file__), db_name)
        print(f"Chemin: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"Le fichier {db_name} n'existe pas")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables trouvées: {[table[0] for table in tables]}")
        
        for table in tables:
            table_name = table[0]
            if table_name == 'sqlite_sequence':
                continue
                
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} enregistrements")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur: {e}")
        return False

if __name__ == "__main__":
    check_database("users.db")
    check_database("admin.db")
