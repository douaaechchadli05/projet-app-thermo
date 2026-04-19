import sqlite3
import os
from datetime import datetime

def create_user_database():
    """Crée la base de données pour les utilisateurs"""
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table des utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Table des calculs des utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nom TEXT NOT NULL,
            date TEXT NOT NULL,
            temperature REAL NOT NULL,
            x1 REAL NOT NULL,
            x2 REAL NOT NULL,
            p1sat REAL NOT NULL,
            p2sat REAL NOT NULL,
            p_bulle REAL NOT NULL,
            y1 REAL NOT NULL,
            y2 REAL NOT NULL,
            somme_yi REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Base de données utilisateurs créée: {db_path}")

def create_admin_database():
    """Crée la base de données pour l'administration"""
    db_path = os.path.join(os.path.dirname(__file__), 'admin.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table des logs de connexion
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            mac_address TEXT,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            logout_time TIMESTAMP,
            session_duration INTEGER,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Table des activités des utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            activity_details TEXT,
            ip_address TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Table des statistiques de heatmap
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS heatmap_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            country TEXT,
            city TEXT,
            activity_count INTEGER DEFAULT 1,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Base de données admin créée: {db_path}")

def init_all_databases():
    """Initialise toutes les bases de données"""
    create_user_database()
    create_admin_database()
    print("Toutes les bases de données ont été initialisées")

if __name__ == '__main__':
    init_all_databases()
