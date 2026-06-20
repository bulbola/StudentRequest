from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import update, or_
from . import db
from .models import Request, RequestComment, StatusHistory, EmployeeCategory, ActivityLog, RequestCategory
from .security import role_required, sanitize_text, validate_csrf_token, log_action, notify_user, ALLOWED_STATUSES
from .services import escalate_overdue_requests

employee_bp = Blueprint('employee', __name__)


def _employee_category_ids(user_id: int):
    return [row.category_id for row in EmployeeCategory.query.filter_by(employee_id=user_id).all()]


def _visible_requests_query():
    query = Request.query.order_by(Request.created_at.desc())
    if current_user.role == 'manager':
        return query
    if current_user.role == 'employee':
        profile = current_user.employee_profile
        if profile and profile.can_process_all:
            return query
        categories = _employee_category_ids(current_user.id)
        if categories:
            return query.filter(Request.category_id.in_(categories))
        return query.filter(Request.assigned_employee_id == current_user.id)
    return query


def _check_employee_can_process(req: Request):
    if current_user.role != 'employee':
        abort(403)
    profile = current_user.employee_profile
    if profile and profile.can_process_all:
        return
    category_ids = _employee_category_ids(current_user.id)
    if req.category_id not in category_ids and req.assigned_employee_id != current_user.id:
        abort(403)


def _create_history(req: Request, old_status: str | None, new_status: str, reason: str | None = None):
    db.session.add(StatusHistory(
        request_id=req.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=current_user.id,
        change_reason=reason,
    ))


@employee_bp.route('/')
@login_required
@role_required('employee', 'manager')
def dashboard():
    status = request.args.get('status')
    query = _visible_requests_query()
    if status:
        query = query.filter_by(status=status)
    requests = query.all()
    now = datetime.utcnow()
    return render_template('employee/dashboard.html', requests=requests, now=now)


@employee_bp.route('/stats')
@login_required
@role_required('manager', 'admin')
def stats():
    total = Request.query.count()
    overdue = Request.query.filter(Request.sla_due_at < datetime.utcnow(), Request.status.in_(['created', 'in_progress', 'needs_info'])).count()
    by_status = {s: Request.query.filter_by(status=s).count() for s in ['created', 'in_progress', 'needs_info', 'processed', 'closed', 'rejected']}
    by_category = dict(db.session.query(RequestCategory.name, db.func.count(Request.id)).join(RequestCategory, RequestCategory.id == Request.category_id).group_by(RequestCategory.name).all())
    log_count = ActivityLog.query.count()
    return render_template('employee/stats.html', total=total, overdue=overdue, by_status=by_status, by_category=by_category, log_count=log_count)


@employee_bp.route('/requests/<int:request_id>/take', methods=['POST'])
@login_required
@role_required('employee')
def take_request(request_id):
    validate_csrf_token(request.form.get('_csrf_token'))
    req = db.session.get(Request, request_id) or abort(404)
    _check_employee_can_process(req)
    old_status = req.status
    now = datetime.utcnow()
    new_status = 'in_progress' if old_status == 'created' else old_status
    result = db.session.execute(
        update(Request)
        .where(Request.id == request_id)
        .where(or_(Request.locked_by_id.is_(None), Request.locked_by_id == current_user.id))
        .values(
            locked_by_id=current_user.id,
            assigned_employee_id=current_user.id,
            locked_at=now,
            status=new_status,
            updated_at=now,
        )
    )
    if result.rowcount != 1:
        db.session.rollback()
        abort(409, description='Заявка уже взята в работу другим сотрудником')
    req = db.session.get(Request, request_id)
    if old_status != new_status:
        _create_history(req, old_status, new_status, 'Заявка взята в работу')
    log_action(current_user.id, 'take_request', 'request', req.id)
    notify_user(req.student_id, 'Статус заявки изменен', f'Заявка №{req.id} взята в работу сотрудником.', req.id)
    db.session.commit()
    flash('Заявка закреплена за вами')
    return redirect(url_for('employee.process_request', request_id=req.id))


@employee_bp.route('/requests/<int:request_id>/escalate', methods=['POST'])
@login_required
@role_required('employee', 'manager')
def escalate_request(request_id):
    validate_csrf_token(request.form.get('_csrf_token'))
    req = db.session.get(Request, request_id) or abort(404)
    if current_user.role == 'employee':
        _check_employee_can_process(req)
    req.escalated_at = datetime.utcnow()
    log_action(current_user.id, 'escalate_request', 'request', req.id)
    notify_user(req.student_id, 'Заявка передана на контроль', f'Заявка №{req.id} просрочена по SLA и передана руководителю.', req.id)
    db.session.commit()
    flash('Заявка передана на контроль руководителю')
    return redirect(url_for('employee.dashboard'))


@employee_bp.route('/sla/check', methods=['POST'])
@login_required
@role_required('manager', 'admin')
def check_sla_now():
    validate_csrf_token(request.form.get('_csrf_token'))
    count = escalate_overdue_requests(current_user.id)
    flash(f'Проверка SLA завершена. Эскалировано заявок: {count}')
    return redirect(url_for('employee.stats'))


@employee_bp.route('/requests/<int:request_id>', methods=['GET', 'POST'])
@login_required
@role_required('employee')
def process_request(request_id):
    req = db.session.get(Request, request_id) or abort(404)
    _check_employee_can_process(req)
    if request.method == 'POST':
        validate_csrf_token(request.form.get('_csrf_token'))
        if req.locked_by_id != current_user.id:
            abort(409, description='Сначала необходимо взять заявку в работу. Если она заблокирована другим сотрудником, обработка запрещена.')
        old_status = req.status
        new_status = request.form.get('status')
        comment_text = sanitize_text(request.form.get('comment_text'), 2000)
        rejection_reason = sanitize_text(request.form.get('rejected_reason'), 500)

        if new_status and new_status not in ALLOWED_STATUSES:
            abort(400, description='Некорректный статус')
        if new_status == 'rejected' and not rejection_reason:
            flash('При отклонении заявки необходимо указать причину.')
            return redirect(url_for('employee.process_request', request_id=req.id))
        if new_status and new_status != old_status:
            req.status = new_status
            if new_status == 'rejected':
                req.rejected_reason = rejection_reason
            if new_status in ('closed', 'rejected'):
                req.locked_by_id = None
                req.locked_at = None
            _create_history(req, old_status, new_status, rejection_reason if new_status == 'rejected' else None)
            notify_user(req.student_id, 'Статус заявки изменен', f'Заявка №{req.id}: новый статус - {new_status}.', req.id)
            log_action(current_user.id, 'change_status', 'request', req.id)
        if comment_text:
            db.session.add(RequestComment(request_id=req.id, user_id=current_user.id, comment_text=comment_text))
            notify_user(req.student_id, 'Новый комментарий к заявке', f'По заявке №{req.id} добавлен комментарий сотрудника.', req.id)
            log_action(current_user.id, 'add_comment', 'request', req.id)
        db.session.commit()
        flash('Заявка обновлена')
        return redirect(url_for('employee.dashboard'))
    comments = RequestComment.query.filter_by(request_id=request_id).order_by(RequestComment.created_at.asc()).all()
    history = StatusHistory.query.filter_by(request_id=request_id).order_by(StatusHistory.changed_at.asc()).all()
    return render_template('employee/process_request.html', req=req, comments=comments, history=history)
