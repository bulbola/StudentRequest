from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('shared/index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    if current_user.role == 'employee':
        return redirect(url_for('employee.dashboard'))
    return redirect(url_for('student.dashboard'))

@main_bp.route('/help')
def help_page():
    return render_template('shared/help.html')
