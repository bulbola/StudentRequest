from flask import Blueprint, render_template, Response, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from openpyxl import Workbook
from io import BytesIO
from werkzeug.security import generate_password_hash
from .models import User, Request, RequestCategory, ActivityLog, StudentProfile, EmployeeProfile, EmployeeCategory
from .security import role_required, log_action, validate_csrf_token, sanitize_text, ALLOWED_ROLES
from .validators import validate_email
from . import db

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@login_required
@role_required('admin')
def dashboard():
    stats = {
        'users': User.query.count(),
        'requests': Request.query.count(),
        'created': Request.query.filter_by(status='created').count(),
        'closed': Request.query.filter_by(status='closed').count(),
        'overdue': Request.query.filter(Request.sla_due_at < db.func.now(), Request.status.in_(['created', 'in_progress', 'needs_info'])).count(),
        'logs': ActivityLog.query.count(),
    }
    return render_template('admin/dashboard.html', stats=stats)


@admin_bp.route('/users')
@login_required
@role_required('admin')
def users():
    return render_template('admin/users.html', users=User.query.order_by(User.full_name).all())


def _ensure_profile(user: User, form):
    if user.role == 'student' and not user.student_profile:
        db.session.add(StudentProfile(
            user_id=user.id,
            group_name=sanitize_text(form.get('group_name') or 'Не указана', 30),
            course=int(form.get('course') or 1),
            direction=sanitize_text(form.get('direction') or 'Бизнес-информатика', 180),
        ))
    if user.role == 'employee':
        profile = user.employee_profile
        if not profile:
            profile = EmployeeProfile(user_id=user.id, position='специалист', department='структурное подразделение Университета')
            db.session.add(profile)
        profile.position = sanitize_text(form.get('position') or profile.position or 'специалист', 120)
        profile.department = sanitize_text(form.get('department') or profile.department or 'структурное подразделение Университета', 180)
        profile.can_process_all = form.get('can_process_all') == 'on'
        EmployeeCategory.query.filter_by(employee_id=user.id).delete()
        if not profile.can_process_all:
            for cid in form.getlist('category_ids'):
                if cid.isdigit():
                    db.session.add(EmployeeCategory(employee_id=user.id, category_id=int(cid)))


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_user():
    categories = RequestCategory.query.order_by(RequestCategory.name).all()
    if request.method == 'POST':
        validate_csrf_token(request.form.get('_csrf_token'))
        full_name = sanitize_text(request.form.get('full_name'), 180)
        email = (request.form.get('email') or '').strip().lower()
        role = request.form.get('role') or 'student'
        password = request.form.get('password') or ''
        errors = []
        if len(full_name) < 3:
            errors.append('ФИО должно содержать не менее 3 символов.')
        if not validate_email(email):
            errors.append('Некорректный email.')
        if role not in ALLOWED_ROLES:
            errors.append('Некорректная роль.')
        if len(password) < 8:
            errors.append('Пароль должен содержать не менее 8 символов.')
        if User.query.filter_by(email=email).first():
            errors.append('Пользователь с таким email уже существует.')
        if errors:
            for e in errors:
                flash(e)
            return render_template('admin/user_form.html', user=None, categories=categories), 400
        user = User(full_name=full_name, email=email, role=role, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.flush()
        _ensure_profile(user, request.form)
        log_action(current_user.id, 'create_user', 'user', user.id)
        db.session.commit()
        flash('Пользователь создан')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', user=None, categories=categories)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    user = db.session.get(User, user_id) or abort(404)
    categories = RequestCategory.query.order_by(RequestCategory.name).all()
    if request.method == 'POST':
        validate_csrf_token(request.form.get('_csrf_token'))
        full_name = sanitize_text(request.form.get('full_name'), 180)
        role = request.form.get('role') or user.role
        if len(full_name) < 3 or role not in ALLOWED_ROLES:
            flash('Проверьте ФИО и роль пользователя.')
            return render_template('admin/user_form.html', user=user, categories=categories), 400
        user.full_name = full_name
        user.role = role
        user.is_active_flag = request.form.get('is_active_flag') == 'on'
        password = request.form.get('password') or ''
        if password:
            if len(password) < 8:
                flash('Пароль должен содержать не менее 8 символов.')
                return render_template('admin/user_form.html', user=user, categories=categories), 400
            user.password_hash = generate_password_hash(password)
        _ensure_profile(user, request.form)
        log_action(current_user.id, 'edit_user', 'user', user.id)
        db.session.commit()
        flash('Пользователь обновлен')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', user=user, categories=categories)


@admin_bp.route('/categories')
@login_required
@role_required('admin')
def categories():
    return render_template('admin/categories.html', categories=RequestCategory.query.order_by(RequestCategory.name).all())


@admin_bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_category():
    if request.method == 'POST':
        validate_csrf_token(request.form.get('_csrf_token'))
        name = sanitize_text(request.form.get('name'), 120)
        description = sanitize_text(request.form.get('description'), 1000)
        if len(name) < 3:
            flash('Название категории должно содержать не менее 3 символов.')
            return render_template('admin/category_form.html', category=None), 400
        category = RequestCategory(name=name, description=description, is_active=request.form.get('is_active') == 'on')
        db.session.add(category)
        db.session.flush()
        log_action(current_user.id, 'create_category', 'category', category.id)
        db.session.commit()
        flash('Категория создана')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', category=None)


@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_category(category_id):
    category = db.session.get(RequestCategory, category_id) or abort(404)
    if request.method == 'POST':
        validate_csrf_token(request.form.get('_csrf_token'))
        name = sanitize_text(request.form.get('name'), 120)
        if len(name) < 3:
            flash('Название категории должно содержать не менее 3 символов.')
            return render_template('admin/category_form.html', category=category), 400
        category.name = name
        category.description = sanitize_text(request.form.get('description'), 1000)
        category.is_active = request.form.get('is_active') == 'on'
        log_action(current_user.id, 'edit_category', 'category', category.id)
        db.session.commit()
        flash('Категория обновлена')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', category=category)


@admin_bp.route('/reports/requests.xlsx')
@login_required
@role_required('admin')
def export_requests():
    wb = Workbook()
    ws = wb.active
    ws.title = 'Заявки'
    ws.append(['ID', 'Тема', 'Категория', 'Статус', 'Приоритет', 'SLA до', 'Исполнитель', 'Дата создания'])
    for req in Request.query.order_by(Request.created_at.desc()).all():
        ws.append([
            req.id,
            req.title,
            req.category.name,
            req.status,
            req.priority,
            req.sla_due_at.strftime('%d.%m.%Y %H:%M') if req.sla_due_at else '',
            req.assigned_employee.full_name if req.assigned_employee else '',
            req.created_at.strftime('%d.%m.%Y %H:%M'),
        ])
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    log_action(current_user.id, 'export_requests_xlsx', 'report', None)
    db.session.commit()
    return Response(
        bio.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=requests.xlsx'},
    )
