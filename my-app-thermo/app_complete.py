from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
import sqlite3
import os
import hashlib
import re
from datetime import datetime, timedelta
import socket
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Constantes d'Antoine pour les calculs thermodynamiques
ANTOINE = {
    'benzene': {'A': 6.90565, 'B': 1211.033, 'C': 220.790},   # NIST
    'toluene': {'A': 6.95334, 'B': 1343.943, 'C': 219.377},   # NIST
}

def antoine_psat_mmhg(composant, T_celsius):
    """
    Calcule la pression de vapeur saturante (mmHg) via la loi d'Antoine.
    log10(Psat) = A - B / (C + T)
    """
    c = ANTOINE[composant]
    log_p = c['A'] - c['B'] / (c['C'] + T_celsius)
    return 10 ** log_p

def mmhg_to_kpa(p_mmhg):
    """Convertit mmHg en kPa (1 mmHg = 0.133322 kPa)"""
    return p_mmhg * 0.133322

def calculer_psat(T_celsius):
    """
    Retourne P1sat (benzène) et P2sat (toluène) en kPa pour une température T.
    """
    p1_mmhg = antoine_psat_mmhg('benzene', T_celsius)
    p2_mmhg = antoine_psat_mmhg('toluene', T_celsius)
    p1_kpa  = round(mmhg_to_kpa(p1_mmhg), 3)
    p2_kpa  = round(mmhg_to_kpa(p2_mmhg), 3)
    return p1_kpa, p2_kpa

def calculer_raoult(x1, x2, p1_sat, p2_sat):
    """
    Calcule tous les paramètres de la loi de Raoult
    """
    p_bulle  = round(x1 * p1_sat + x2 * p2_sat, 4)
    y1       = round((x1 * p1_sat) / p_bulle, 4)
    y2       = round((x2 * p2_sat) / p_bulle, 4)
    somme_yi = round(y1 + y2, 4)
    return {
        'p_bulle':  p_bulle,
        'terme1':   round(x1 * p1_sat, 4),
        'terme2':   round(x2 * p2_sat, 4),
        'y1':       y1,
        'y2':       y2,
        'somme_yi': somme_yi,
        'verif_ok': abs(somme_yi - 1.0) < 0.001
    }

app = Flask(__name__)
app.secret_key = 'cle_secrete_thermo_2024_secure'

# Configuration du timeout de session (1 minute)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1)

# Configuration Gmail
GMAIL_EMAIL = "thermocalc.app@gmail.com"
GMAIL_PASSWORD = "votre_mot_de_passe_app"  # À configurer avec un mot de passe d'application Gmail

def send_password_email(email, password, username):
    """Envoie le mot de passe par email via Gmail"""
    try:
        # Création du message
        msg = MIMEMultipart()
        msg['From'] = GMAIL_EMAIL
        msg['To'] = email
        msg['Subject'] = "ThermoCalc - Récupération de votre mot de passe"
        
        # Corps du message
        body = f"""
        Bonjour {username},
        
        Vous avez demandé la récupération de votre mot de passe pour ThermoCalc.
        
        Voici vos identifiants de connexion :
        - Nom d'utilisateur : {username}
        - Mot de passe : {password}
        
        Vous pouvez maintenant vous connecter sur : http://127.0.0.1:5000/login
        
        Si vous n'avez pas demandé cette récupération, veuillez ignorer cet email.
        
        Cordialement,
        L'équipe ThermoCalc
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Envoi via Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(GMAIL_EMAIL, email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")
        return False

# Configuration des bases de données
USERS_DB = os.path.join(os.path.dirname(__file__), 'users.db')
ADMIN_DB = os.path.join(os.path.dirname(__file__), 'admin.db')

# Configuration Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = str(id)
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email FROM users WHERE id = ? AND is_active = 1', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None

def get_client_info():
    """Récupère les informations du client"""
    # IP address
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        ip = request.remote_addr or '127.0.0.1'
    
    # User Agent
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Générer un MAC address simulé pour la démo
    mac_address = ':'.join(['{:02x}'.format(uuid.getnode() >> elements) for elements in range(0, 48, 8)][::-1])
    
    return ip, mac_address, user_agent

def log_user_activity(user_id, username, activity_type, activity_details=None):
    """Enregistre l'activité d'un utilisateur"""
    ip, mac_address, user_agent = get_client_info()
    
    conn = sqlite3.connect(ADMIN_DB)
    cursor = conn.cursor()
    
    # Enregistrer l'activité
    cursor.execute('''
        INSERT INTO user_activities (user_id, username, activity_type, activity_details, ip_address)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, activity_type, activity_details, ip))
    
    # Mettre à jour les données de heatmap
    cursor.execute('''
        INSERT OR REPLACE INTO heatmap_data 
        (user_id, username, ip_address, activity_count, last_activity)
        VALUES (?, ?, ?, 
            COALESCE((SELECT activity_count FROM heatmap_data WHERE user_id = ?), 0) + 1,
            CURRENT_TIMESTAMP)
    ''', (user_id, username, ip, user_id))
    
    conn.commit()
    conn.close()

def log_user_session(user_id, username, action='login'):
    """Enregistre les sessions de connexion/déconnexion"""
    ip, mac_address, user_agent = get_client_info()
    
    conn = sqlite3.connect(ADMIN_DB)
    cursor = conn.cursor()
    
    if action == 'login':
        cursor.execute('''
            INSERT INTO user_sessions (user_id, username, ip_address, mac_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, ip, mac_address, user_agent))
    elif action == 'logout':
        # Mettre à jour le temps de déconnexion
        cursor.execute('''
            UPDATE user_sessions 
            SET logout_time = CURRENT_TIMESTAMP,
                session_duration = (julianday(CURRENT_TIMESTAMP) - julianday(login_time)) * 86400
            WHERE user_id = ? AND logout_time IS NULL
        ''', (user_id,))
    
    conn.commit()
    conn.close()

# Routes principales
@app.route('/')
def index():
    return render_template('index_modern_new.html', current_user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login_modern_new.html', error='Veuillez remplir tous les champs')
        
        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, email, password_hash FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        
        conn.close()
        
        if user_data:
            # Vérifier le mot de passe
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if hashed_password == user_data[3]:
                user = User(user_data[0], user_data[1], user_data[2])
                session.permanent = True  # Activer la session permanente
                login_user(user)
                
                # Enregistrer la connexion
                log_user_session(user_data[0], username, 'login')
                log_user_activity(user_data[0], username, 'login', 'Connexion réussie')
                
                # Debug: vérifier si l'utilisateur est bien connecté
                print(f"DEBUG: Utilisateur connecté: {user.username}, ID: {user.id}")
                print(f"DEBUG: is_authenticated: {current_user.is_authenticated}")
                
                # Rediriger admin vers le dashboard admin, les autres vers /calcul
                if username == 'admin':
                    return redirect('/admin')
                else:
                    return redirect('/calcul')
            else:
                return render_template('login_modern_new.html', error='Mot de passe incorrect')
        else:
            return render_template('login_modern_new.html', 
                                 error=f'L\'identifiant "{username}" n\'existe pas. <a href="/register">Créez un compte</a> pour continuer.')
    
    return render_template('login_modern_new.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            return render_template('forgot_password.html', error='Veuillez entrer votre adresse email')
        
        # Rechercher l'utilisateur par email
        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM users WHERE email = ?", (email,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            # Récupérer le mot de passe original (pour la démo, on utilise une version simplifiée)
            # Note: En production, il faudrait implémenter un système de réinitialisation sécurisé
            password = "demo123"  # Pour la démo, on envoie un mot de passe par défaut
            
            # Envoyer l'email
            if send_password_email(email, password, user_data[1]):
                return render_template('forgot_password.html', 
                                     success='Un email avec votre mot de passe a été envoyé à ' + email)
            else:
                return render_template('forgot_password.html', 
                                     error='Erreur lors de l\'envoi de l\'email. Veuillez réessayer.')
        else:
            return render_template('forgot_password.html', 
                                 error='Aucun compte trouvé avec cette adresse email')
    
    return render_template('forgot_password.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Si l'utilisateur est déjà connecté, le rediriger vers la page de calcul
    if current_user.is_authenticated:
        return redirect('/calcul')
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation des champs
        if not username or not email or not password or not confirm_password:
            return render_template('register_modern_new.html', error='Tous les champs sont obligatoires')
        
        if password != confirm_password:
            return render_template('register_modern_new.html', error='Les mots de passe ne correspondent pas')
        
        # Validation du mot de passe
        if len(password) < 6:
            return render_template('register_modern_new.html', error='Le mot de passe doit contenir au moins 6 caractères')
        
        if not re.search(r'[A-Z]', password):
            return render_template('register_modern_new.html', error='Le mot de passe doit contenir au moins une majuscule')
        
        if not re.search(r'[a-z]', password):
            return render_template('register_modern_new.html', error='Le mot de passe doit contenir au moins une minuscule')
        
        if not re.search(r'\d', password):
            return render_template('register_modern_new.html', error='Le mot de passe doit contenir au moins un chiffre')
        
        # Validation de l'email
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            return render_template('register_modern_new.html', error='Veuillez entrer une adresse email valide')
        
        # Validation du nom d'utilisateur
        username_regex = r'^[a-zA-Z0-9_]{3,20}$'
        if not re.match(username_regex, username):
            return render_template('register_modern_new.html', error='Le nom d\'utilisateur doit contenir 3-20 caractères (lettres, chiffres, underscore)')
        
        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        
        # Vérifier si l'utilisateur existe déjà
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return render_template('register_modern_new.html', error='Nom d\'utilisateur déjà pris')
        
        # Vérifier si l'email existe déjà
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return render_template('register_modern_new.html', error='Cette adresse email est déjà utilisée')
        
        # Hasher le mot de passe
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Insérer le nouvel utilisateur
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                      (username, email, hashed_password))
        
        user_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # Message de succès et redirection
        success_message = f'Compte créé avec succès pour {username}! Vous pouvez maintenant vous connecter.'
        return render_template('login_modern_new.html', success=success_message)
    
    return render_template('register_modern_new.html')

@app.route('/logout')
@login_required
def logout():
    # Enregistrer la déconnexion
    log_user_session(current_user.id, current_user.username, 'logout')
    log_user_activity(current_user.id, current_user.username, 'logout', 'Déconnexion')
    
    logout_user()
    return redirect('/')

@app.route('/calcul')
@login_required
def calcul():
    print(f"DEBUG: Route /calcul appelée, utilisateur: {current_user.username}")
    print(f"DEBUG: is_authenticated dans /calcul: {current_user.is_authenticated}")
    log_user_activity(current_user.id, current_user.username, 'page_access', 'Accès page calcul')
    return render_template('calcul_modern_new.html')

@app.route('/historique')
@login_required
def historique_page():
    log_user_activity(current_user.id, current_user.username, 'page_access', 'Accès page historique')
    
    # Récupérer les calculs de l'utilisateur connecté
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM user_calculations WHERE user_id = ? ORDER BY id DESC', 
                       (current_user.id,)).fetchall()
    conn.close()
    
    return render_template('historique_modern.html', calculations=rows)

@app.route('/admin-access')
def admin_access():
    """Route d'accès admin qui gère la redirection après connexion"""
    if current_user.is_authenticated:
        # Si déjà connecté, vérifier si c'est admin
        if current_user.username == 'admin':
            return redirect('/admin')
        else:
            return redirect('/calcul')
    else:
        # Si non connecté, rediriger vers login avec next=admin
        return redirect('/login?next=admin')

@app.route('/admin')
@login_required
def admin():
    # Vérifier si c'est l'admin admin/admin123 uniquement
    if current_user.username != 'admin':
        return redirect('/calcul')
    
    log_user_activity(current_user.id, current_user.username, 'admin_access', 'Accès panneau admin')
    return render_template('admin_dashboard.html')

@app.route('/calculer', methods=['POST'])
@login_required
def calculer():
    data = request.get_json()
    try:
        nom = str(data.get('nom', 'Sans nom')).strip() or 'Sans nom'
        T = float(data['temperature'])
        x1 = float(data['x1'])
        x2 = float(data['x2'])
        
        # Validation améliorée
        if abs((x1 + x2) - 1.0) > 0.01:
            return jsonify({'erreur': f'x1 + x2 doit être égal à 1. Actuellement : {round(x1+x2,3)}'}), 400
        if x1 < 0 or x2 < 0 or x1 > 1 or x2 > 1:
            return jsonify({'erreur': 'Les fractions molaires doivent être comprises entre 0 et 1.'}), 400
        if T < 0 or T > 200:
            return jsonify({'erreur': 'Température doit être entre 0 et 200 °C.'}), 400
        
        # Calculs avec Antoine (fonctions intégrées)
        p1_sat, p2_sat = calculer_psat(T)
        
        # Calculs détaillés en mmHg pour affichage
        p1_mmhg = round(antoine_psat_mmhg('benzene', T), 1)
        p2_mmhg = round(antoine_psat_mmhg('toluene', T), 1)
        
        # Calculs Raoult complets
        r = calculer_raoult(x1, x2, p1_sat, p2_sat)
        
        p_bulle = r['p_bulle']
        y1 = r['y1']
        y2 = r['y2']
        somme_yi = r['somme_yi']
        
        # Sauvegarde dans la base utilisateurs
        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_calculations
                (user_id, nom, date, temperature, x1, x2, p1sat, p2sat, p_bulle, y1, y2, somme_yi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user.id, nom, datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            T, x1, x2, p1_sat, p2_sat,
            p_bulle, y1, y2, somme_yi
        ))
        conn.commit()
        conn.close()
        
        # Enregistrer l'activité
        log_user_activity(current_user.id, current_user.username, 'calcul', f'Calcul {nom}')
        
        return jsonify({
            'nom': nom,
            'temperature': T,
            'x1': x1,
            'x2': x2,
            'antoine': {
                'p1sat_kpa': p1_sat,
                'p2sat_kpa': p2_sat,
                'p1sat_mmhg': p1_mmhg,
                'p2sat_mmhg': p2_mmhg,
            },
            'resultats': {
                'p_bulle': p_bulle,
                'terme1': r['terme1'],
                'terme2': r['terme2'],
                'y1': y1,
                'y2': y2,
                'somme_yi': somme_yi,
                'verif_ok': r['verif_ok']
            }
        })
        
    except Exception as e:
        return jsonify({'erreur': f'Données invalides : {str(e)}'}), 400

@app.route('/historique-api', methods=['GET'])
@login_required
def historique():
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM user_calculations WHERE user_id = ? ORDER BY id DESC', 
                       (current_user.id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/admin/sessions', methods=['GET'])
@login_required
def admin_sessions():
    if current_user.username != 'admin':
        return jsonify({'erreur': 'Accès non autorisé'}), 403
    
    conn = sqlite3.connect(ADMIN_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM user_sessions ORDER BY login_time DESC LIMIT 100').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/admin/heatmap', methods=['GET'])
@login_required
def admin_heatmap():
    if current_user.username != 'admin':
        return jsonify({'erreur': 'Accès non autorisé'}), 403
    
    conn = sqlite3.connect(ADMIN_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM heatmap_data ORDER BY activity_count DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/admin/activities', methods=['GET'])
@login_required
def admin_activities():
    if current_user.username != 'admin':
        return jsonify({'erreur': 'Accès non autorisé'}), 403
    
    conn = sqlite3.connect(ADMIN_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM user_activities ORDER BY timestamp DESC LIMIT 50').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/geolocate/<ip>')
def geolocate_ip_api(ip):
    """API améliorée pour géolocaliser une adresse IP avec plusieurs sources"""
    try:
        import requests
        
        # Liste des APIs à essayer (fallback)
        apis = [
            {
                'url': f'http://ip-api.com/json/{ip}',
                'parse': lambda data: {
                    'lat': data['lat'],
                    'lon': data['lon'],
                    'country': data['country'],
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'isp': data.get('isp', 'Unknown')
                }
            },
            {
                'url': f'http://ipinfo.io/{ip}/json',
                'parse': lambda data: {
                    'lat': float(data.get('loc', '0,0').split(',')[0]) if data.get('loc') else 0,
                    'lon': float(data.get('loc', '0,0').split(',')[1]) if data.get('loc') else 0,
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('region', 'Unknown'),
                    'isp': data.get('org', 'Unknown')
                }
            }
        ]
        
        # Essayer chaque API
        for api in apis:
            try:
                response = requests.get(api['url'], timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Vérifier si la réponse est valide
                    if 'status' in data and data['status'] == 'success':
                        parsed_data = api['parse'](data)
                        return jsonify({
                            'success': True,
                            'source': 'ip-api.com',
                            **parsed_data
                        })
                    elif 'country' in data:  # ipinfo.io format
                        parsed_data = api['parse'](data)
                        if parsed_data['lat'] != 0 and parsed_data['lon'] != 0:
                            return jsonify({
                                'success': True,
                                'source': 'ipinfo.io',
                                **parsed_data
                            })
            except Exception as api_error:
                print(f"Erreur API {api['url']}: {api_error}")
                continue
        
        # Si toutes les APIs échouent, retourner une position par défaut
        return jsonify({
            'success': False,
            'lat': 33.5922,
            'lon': -7.6184,
            'country': 'Morocco',
            'city': 'Casablanca',
            'region': 'Casablanca-Settat',
            'isp': 'Local',
            'error': 'All APIs failed'
        })
            
    except Exception as e:
        print(f"Erreur de géolocalisation pour {ip}: {e}")
        return jsonify({
            'success': False,
            'lat': 33.5922,
            'lon': -7.6184,
            'country': 'Morocco',
            'city': 'Casablanca',
            'region': 'Casablanca-Settat',
            'isp': 'Local',
            'error': str(e)
        })

# Fonctions utilitaires
def create_admin():
    """Crée un utilisateur administrateur par défaut"""
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    
    password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash)
        VALUES (?, ?, ?)
    ''', ('admin', 'admin@thermo.com', password_hash))
    
    conn.commit()
    conn.close()
    print("Admin créé: admin / admin123")

def init_db():
    """Initialise toutes les bases de données"""
    from database_setup import init_all_databases
    init_all_databases()
    create_admin()

if __name__ == '__main__':
    init_db()
    print("Application démarrée sur http://127.0.0.1:5000")
    print("Login admin: admin / admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)
