from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class PressionSaturante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    composant = db.Column(db.String(50), nullable=False)  # 'benzene' or 'toluene'
    temperature = db.Column(db.Float, nullable=False)  # °C
    pression = db.Column(db.Float, nullable=False)  # kPa

class Utilisateur(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), default='user')  # 'user' or 'admin'
    reset_token = db.Column(db.String(128), nullable=True)
    reset_expiration = db.Column(db.DateTime, nullable=True)
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)

class LogsAuth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    mac_address = db.Column(db.String(17), nullable=True)
    date_auth = db.Column(db.DateTime, default=datetime.utcnow)
    pays = db.Column(db.String(100), nullable=True)
    ville = db.Column(db.String(100), nullable=True)
    lat = db.Column(db.Float, nullable=True)
    lon = db.Column(db.Float, nullable=True)

class HistoriqueCalculs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    fraction_toluene = db.Column(db.Float, nullable=False)
    fraction_benzene = db.Column(db.Float, nullable=False)
    pression_toluene = db.Column(db.Float, nullable=False)
    pression_benzene = db.Column(db.Float, nullable=False)
    date_calcul = db.Column(db.DateTime, default=datetime.utcnow)