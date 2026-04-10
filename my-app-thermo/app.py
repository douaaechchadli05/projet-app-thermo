from flask import Flask, render_template
from models import db
from auth import auth
from flask_login import LoginManager
from extensions import mail
from flask_wtf import CSRFProtect

app = Flask(__name__)

app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

# MAIL CONFIG
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_password'

db.init_app(app)
mail.init_app(app)

csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

from models import Utilisateur

@login_manager.user_loader
def load_user(user_id):
    return Utilisateur.query.get(int(user_id))

app.register_blueprint(auth)

# ---------------- ROUTES ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcul')
def calcul():
    return render_template('calcul.html')

@app.route('/admin')
def admin_dashboard():
    return render_template('admin.html')

# ---------------- SECURITY HEADERS ----------------
@app.after_request
def secure_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

if __name__ == "__main__":
    app.run(debug=True)