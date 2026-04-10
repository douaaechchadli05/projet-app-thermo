from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Utilisateur, LogsAuth
from flask_mail import Message
import requests
import uuid
from datetime import datetime, timedelta
import os

auth = Blueprint('auth', __name__)

def get_geo_info(ip):
    try:
        response = requests.get(f'http://ipinfo.io/{ip}/json')
        data = response.json()
        return {
            'pays': data.get('country'),
            'ville': data.get('city'),
            'loc': data.get('loc', '0,0').split(',')
        }
    except:
        return {'pays': None, 'ville': None, 'loc': ['0', '0']}

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Utilisateur.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            # Log the authentication
            ip = request.remote_addr
            geo = get_geo_info(ip)
            log = LogsAuth(
                user_id=user.id,
                ip_address=ip,
                mac_address=request.form.get('mac'),  # From JS
                pays=geo['pays'],
                ville=geo['ville'],
                lat=float(geo['loc'][0]),
                lon=float(geo['loc'][1])
            )
            db.session.add(log)
            db.session.commit()
            return redirect(url_for('main.index'))
        flash('Identifiants invalides')
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = Utilisateur(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Inscription réussie')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Utilisateur.query.filter_by(email=email).first()
        if user:
            token = str(uuid.uuid4())
            user.reset_token = token
            user.reset_expiration = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            # Import mail here to avoid circular import
            from flask import current_app
            mail = current_app.extensions.get('mail')
            msg = Message('Réinitialisation du mot de passe', sender=current_app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Votre token de réinitialisation : {token}'
            try:
                mail.send(msg)
                flash('Email envoyé. Vérifiez votre boîte de réception.')
            except Exception as e:
                flash('Erreur SMTP : vérifiez votre configuration MAIL_USERNAME / MAIL_PASSWORD et votre compte Gmail.')
                current_app.logger.error(f'Erreur mail reset_password: {e}')
        else:
            flash('Email non trouvé')
    return render_template('reset_password.html')

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    user = Utilisateur.query.filter_by(reset_token=token).first()
    if user and user.reset_expiration > datetime.utcnow():
        if request.method == 'POST':
            password = request.form.get('password')
            user.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            user.reset_token = None
            user.reset_expiration = None
            db.session.commit()
            flash('Mot de passe réinitialisé')
            return redirect(url_for('auth.login'))
        return render_template('reset_password_form.html')
    flash('Token invalide ou expiré')
    return redirect(url_for('auth.reset_password'))