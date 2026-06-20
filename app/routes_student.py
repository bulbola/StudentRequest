from datetime import datetime, timedelta
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from . import db
from .models import Request, RequestCategory, RequestFile, RequestComment, StatusHistory
from .security import role_required, sanitize_text, validate_csrf_token, log_action, notify_user
from .services import notify_responsible_on_created
from .validators import validate_request_form

student_bp = Blueprint('student', __name__)


def _sla_due_at(priority: str):
    key = {
        'low': 'SLA_HOURS_LOW',
        'normal': 'SLA_HOURS_NORMAL',
        'high': 'SLA_HOURS_HIGH',
    }.get(priority, 'SLA_HOURS_NORMAL')
    return datetime.utcnow() + timedelta(hours=current_app.config[key])


@student_bp.route('/')
@login_required
@role_required('student')
def dashboard():
    requests = Request.query.filter_by(student_id=current_user.id).order_by(Request.created_at.desc()).all()
    return render_template('student/dashboard.html', requests=requests)


@student_bp.route('/requests/create', methods=['GET', 'POST'])
@login_required
@role_required('student')
def create_request():
    categories = RequestCategory.query.filter_by(is_active=True).order_by(RequestCategory.name).all()
    if request.method == 'POST':
        validate_csrf_token(request.form.get('_csrf_token'))
        file = request.files.get('file')
        errors = validate_request_form(request.form, file)
        category = None
        if not errors:
            category = db.session.get(RequestCategory, int(request.form.get('category_id')))
            if not category or not category.is_active:
                errors.append('Выбранная категория недоступна.')
        if errors:
            for error in errors:
                flash(error)
            return render_template('student/create_request.html', categories=categories), 400

        priority = request.form.get('priority', 'normal')
        req = Request(
            student_id=current_user.id,
            category_id=category.id,
            title=sanitize_text(request.form.get('title'), 180),
            description=sanitize_text(request.form.get('description'), 4000),
            priority=priority,
            status='created',
            sla_due_at=_sla_due_at(priority),
        )
        db.session.add(req)
        db.session.flush()

        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_dir = Path(current_app.config['UPLOAD_FOLDER'])
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / f'request_{req.id}_{filename}'
            file.save(file_path)
            db.session.add(RequestFile(request_id=req.id, file_name=filename, file_path=str(file_path)))

        db.session.add(StatusHistory(request_id=req.id, old_status=None, new_status='created', changed_by=current_user.id))
        notify_responsible_on_created(req)
        log_action(current_user.id, 'create_request', 'request', req.id)
        db.session.commit()
        flash('Заявка создана')
        return redirect(url_for('student.dashboard'))
    return render_template('student/create_request.html', categories=categories)


@student_bp.route('/requests/<int:request_id>')
@login_required
@role_required('student')
def request_detail(request_id):
    req = db.session.get(Request, request_id) or abort(404)
    if req.student_id != current_user.id:
        abort(403)
    comments = RequestComment.query.filter_by(request_id=request_id).order_by(RequestComment.created_at.asc()).all()
    history = StatusHistory.query.filter_by(request_id=request_id).order_by(StatusHistory.changed_at.asc()).all()
    return render_template('student/request_detail.html', req=req, comments=comments, history=history)


@student_bp.route('/requests/<int:request_id>/resubmit', methods=['POST'])
@login_required
@role_required('student')
def resubmit_request(request_id):
    validate_csrf_token(request.form.get('_csrf_token'))
    req = db.session.get(Request, request_id) or abort(404)
    if req.student_id != current_user.id:
        abort(403)
    if req.status != 'rejected':
        abort(400, description='Повторная подача доступна только для отклоненных заявок')
    old_status = req.status
    req.status = 'created'
    req.rejected_reason = None
    req.locked_by_id = None
    req.locked_at = None
    req.escalated_at = None
    req.sla_due_at = _sla_due_at(req.priority)
    comment_text = sanitize_text(request.form.get('comment_text') or 'Повторная подача заявки после отклонения.', 1000)
    db.session.add(RequestComment(request_id=req.id, user_id=current_user.id, comment_text=comment_text))
    db.session.add(StatusHistory(request_id=req.id, old_status=old_status, new_status='created', changed_by=current_user.id, change_reason='Повторная подача'))
    log_action(current_user.id, 'resubmit_request', 'request', req.id)
    if req.assigned_employee_id:
        notify_user(req.assigned_employee_id, 'Заявка подана повторно', f'Студент повторно подал заявку №{req.id}.', req.id)
    db.session.commit()
    flash('Заявка повторно отправлена на рассмотрение')
    return redirect(url_for('student.request_detail', request_id=req.id))
