from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Utilisateur, LogsAuth, HistoriqueCalculs
from functools import wraps

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = Utilisateur.query.all()
    logs = LogsAuth.query.order_by(LogsAuth.date_auth.desc()).limit(50).all()
    return render_template('admin_dashboard.html', users=users, logs=logs)

@admin.route('/reset_user/<int:user_id>')
@login_required
@admin_required
def reset_user(user_id):
    user = Utilisateur.query.get(user_id)
    if user:
        from werkzeug.security import generate_password_hash
        user.password_hash = generate_password_hash('temp123', method='pbkdf2:sha256')
        db.session.commit()
        flash('Mot de passe réinitialisé à temp123')
    return redirect(url_for('admin.dashboard'))