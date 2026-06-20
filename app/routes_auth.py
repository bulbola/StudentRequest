from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash
from . import db
from .models import User
from .security import log_action, validate_csrf_token
from .validators import validate_email

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        validate_csrf_token(request.form.get('_csrf_token'))
        email = (request.form.get('email') or '').strip().lower()
        if not validate_email(email):
            flash('Введите корректный email')
            return render_template('auth/login.html')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
            log_action(user.id, 'login', 'user', user.id)
            db.session.commit()
            return redirect(url_for('main.dashboard'))
        flash('Неверный email или пароль')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    log_action(user_id, 'logout', 'user', user_id)
    db.session.commit()
    logout_user()
    return redirect(url_for('auth.login'))
