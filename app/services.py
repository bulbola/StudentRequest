from __future__ import annotations

from datetime import datetime
from sqlalchemy import or_

from . import db
from .models import ActivityLog, EmployeeCategory, EmployeeProfile, Notification, Request, User

ACTIVE_PROCESS_STATUSES = ['created', 'in_progress', 'needs_info']


def add_notification(user_id: int, title: str, body: str, request_id: int | None = None, channel: str = 'internal') -> None:
    db.session.add(Notification(user_id=user_id, request_id=request_id, channel=channel, title=title, body=body))


def responsible_employee_ids(category_id: int) -> set[int]:
    """Возвращает сотрудников общей очереди и сотрудников, закрепленных за категорией."""
    employee_ids: set[int] = set()
    for profile in EmployeeProfile.query.join(User, User.id == EmployeeProfile.user_id).filter(
        User.role == 'employee',
        User.is_active_flag.is_(True),
        EmployeeProfile.can_process_all.is_(True),
    ).all():
        employee_ids.add(profile.user_id)
    for row in EmployeeCategory.query.filter_by(category_id=category_id).all():
        if row.employee and row.employee.is_active_flag and row.employee.role == 'employee':
            employee_ids.add(row.employee_id)
    return employee_ids


def notify_responsible_on_created(req: Request) -> None:
    """Внутренние уведомления при создании заявки."""
    for employee_id in responsible_employee_ids(req.category_id):
        add_notification(employee_id, 'Новая заявка', f'Создана новая заявка №{req.id}: {req.title}.', req.id)
    for manager in User.query.filter_by(role='manager', is_active_flag=True).all():
        add_notification(manager.id, 'Новая заявка в подразделении', f'Создана заявка №{req.id} по категории {req.category.name}.', req.id)


def escalate_overdue_requests(actor_user_id: int | None = None) -> int:
    """Помечает просроченные заявки и уведомляет руководителей.

    Функция предназначена для запуска из CLI/cron: `flask check-sla`.
    """
    now = datetime.utcnow()
    overdue = Request.query.filter(
        Request.sla_due_at.isnot(None),
        Request.sla_due_at < now,
        Request.escalated_at.is_(None),
        Request.status.in_(ACTIVE_PROCESS_STATUSES),
    ).all()
    managers = User.query.filter_by(role='manager', is_active_flag=True).all()
    for req in overdue:
        req.escalated_at = now
        for manager in managers:
            add_notification(manager.id, 'Просрочена SLA по заявке', f'Заявка №{req.id} просрочена и передана на контроль.', req.id)
        add_notification(req.student_id, 'Заявка передана на контроль', f'Заявка №{req.id} просрочена по SLA и передана руководителю.', req.id)
        db.session.add(ActivityLog(
            user_id=actor_user_id,
            action='auto_escalate_sla',
            entity_type='request',
            entity_id=req.id,
            ip_address='system',
        ))
    db.session.commit()
    return len(overdue)
