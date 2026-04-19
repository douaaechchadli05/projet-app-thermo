import sqlite3
import os

def show_database_structure(db_name, title):
    print(f'\n=== {title} ===')
    print(f'Fichier: {db_name}')
    print(f'Taille: {os.path.getsize(db_name)} bytes')
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Lister les tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
    
    print(f'Tables: {tables}')
    
    for table in tables:
        print(f'\n--- Table: {table} ---')
        
        # Structure de la table
        cursor.execute(f'PRAGMA table_info({table})')
        columns = cursor.fetchall()
        print('Colonnes:')
        for col in columns:
            null_str = "NOT NULL" if col[3] else "NULL"
            pk_str = " PRIMARY KEY" if col[5] else ""
            print(f'  {col[1]} {col[2]} ({null_str}{pk_str})')
        
        # Nombre d'enregistrements
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f'Enregistrements: {count}')
        
        # Afficher quelques exemples si disponible
        if count > 0:
            cursor.execute(f'SELECT * FROM {table} LIMIT 3')
            rows = cursor.fetchall()
            print('Exemples:')
            for i, row in enumerate(rows):
                print(f'  {i+1}: {row}')
    
    conn.close()

if __name__ == "__main__":
    show_database_structure('users.db', 'BASE DE DONNÉES UTILISATEURS')
    show_database_structure('admin.db', 'BASE DE DONNÉES ADMIN')
