import sqlite3

def check_database(db_name):
    print(f"\n=== Vérification de {db_name} ===")
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Lister les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables: {[table[0] for table in tables]}")
        
        # Vérifier les données dans chaque table
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} enregistrements")
            
            if count > 0 and table_name in ['users', 'user_sessions', 'user_activities']:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                print(f"    Exemples: {rows}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur: {e}")
        return False

if __name__ == "__main__":
    check_database("users.db")
    check_database("admin.db")
