from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'cle_secrete_thermo_2024'
DB_PATH = os.path.join(os.path.dirname(__file__), 'calculs.db')

# Configuration Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username=None, email=None):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    # Pour cette version simple, on utilise des utilisateurs en dur
    if user_id == '1':
        return User('1', 'admin', 'admin@example.com')
    return None

# Base de données
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calculs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
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
            somme_yi REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Routes avec templates modernes
@app.route('/')
def index():
    return render_template('index_modern.html')

@app.route('/calcul')
@login_required
def calcul():
    return render_template('calcul_moderne.html')

@app.route('/historique')
@login_required
def historique_page():
    return render_template('historique_modern.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Login simple pour test
        if username == 'admin' and password == 'admin':
            user = User('1', username, 'admin@example.com')
            login_user(user)
            return redirect('/calcul')
        else:
            return render_template('login.html', error='Identifiants incorrects')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Simple redirection vers login pour cette version
        return redirect('/login')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

@app.route('/test-auth')
def test_auth():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user_id': current_user.id,
            'username': getattr(current_user, 'username', 'Unknown'),
            'message': 'Utilisateur authentifié'
        })
    else:
        return jsonify({
            'authenticated': False,
            'message': 'Utilisateur non authentifié'
        })

@app.route('/calculer', methods=['POST'])
@login_required
def calculer():
    data = request.get_json()
    try:
        nom = str(data.get('nom', 'Sans nom')).strip() or 'Sans nom'
        T = float(data['temperature'])
        x1 = float(data['x1'])
        x2 = float(data['x2'])
        
        # Validation
        if abs((x1 + x2) - 1.0) > 0.001:
            return jsonify({'erreur': f'x1 + x2 doit être égal à 1. Actuellement : {round(x1+x2,4)}'}), 400
        if x1 < 0 or x2 < 0 or x1 > 1 or x2 > 1:
            return jsonify({'erreur': 'Les fractions molaires doivent être comprises entre 0 et 1.'}), 400
        if T < -50 or T > 300:
            return jsonify({'erreur': 'Température doit être entre -50 et 300 °C.'}), 400
        
        # Calculs réels avec les constantes d'Antoine
        def antoine_pressure(A, B, C, T):
            """Calcule la pression de saturation avec l'équation d'Antoine"""
            log10_P = A - B / (C + T)
            P_mmhg = 10 ** log10_P
            P_kpa = P_mmhg * 0.133322  # Conversion mmHg -> kPa
            return P_kpa
        
        # Constantes d'Antoine
        p1_sat = antoine_pressure(6.90565, 1211.033, 220.790, T)  # Benzène
        p2_sat = antoine_pressure(6.95334, 1343.943, 219.377, T)  # Toluène
        
        # Calcul selon la loi de Raoult
        p_bulle = x1 * p1_sat + x2 * p2_sat
        y1 = (x1 * p1_sat) / p_bulle
        y2 = (x2 * p2_sat) / p_bulle
        somme_yi = y1 + y2
        
        # Sauvegarde avec user_id
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO calculs
                    (user_id, nom, date, temperature, x1, x2, p1sat, p2sat, p_bulle, y1, y2, somme_yi)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                current_user.id, nom, datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                T, x1, x2, p1_sat, p2_sat,
                p_bulle, y1, y2, somme_yi
            ))
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            return jsonify({'erreur': f'Erreur base de données : {str(e)}'}), 500
        finally:
            if conn:
                conn.close()
        
        return jsonify({
            'antoine': {
                'p1sat_kpa': p1_sat,
                'p2sat_kpa': p2_sat,
                'p1sat_mmhg': round(antoine_pressure(6.90565, 1211.033, 220.790, T) / 0.133322, 1),
                'p2sat_mmhg': round(antoine_pressure(6.95334, 1343.943, 219.377, T) / 0.133322, 1)
            },
            'resultats': {
                'p_bulle': p_bulle,
                'y1': y1,
                'y2': y2,
                'somme_yi': somme_yi
            }
        })
        
    except Exception as e:
        return jsonify({'erreur': f'Données invalides : {str(e)}'}), 400

@app.route('/historique-api', methods=['GET'])
@login_required
def historique():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        # Ne récupérer que les calculs de l'utilisateur connecté
        rows = conn.execute('SELECT * FROM calculs WHERE user_id = ? ORDER BY id DESC', (current_user.id,)).fetchall()
        return jsonify([dict(r) for r in rows])
    except sqlite3.Error as e:
        return jsonify({'erreur': f'Erreur base de données : {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/historique/<int:calc_id>', methods=['DELETE'])
@login_required
def supprimer(calc_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Vérifier que le calcul appartient à l'utilisateur
        cursor.execute('DELETE FROM calculs WHERE id = ? AND user_id = ?', (calc_id, current_user.id))
        if cursor.rowcount == 0:
            return jsonify({'erreur': 'Calcul non trouvé ou non autorisé'}), 404
        conn.commit()
        return jsonify({'message': 'Calcul supprimé'})
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return jsonify({'erreur': f'Erreur base de données : {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/historique/tout', methods=['DELETE'])
@login_required
def supprimer_tout():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Supprimer seulement les calculs de l'utilisateur
        cursor.execute('DELETE FROM calculs WHERE user_id = ?', (current_user.id,))
        conn.commit()
        return jsonify({'message': 'Historique utilisateur supprimé'})
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return jsonify({'erreur': f'Erreur base de données : {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    init_db()
    print("Application démarrée sur http://127.0.0.1:5000")
    print("Login: admin / admin")
    app.run(debug=True, host='0.0.0.0', port=5000)
