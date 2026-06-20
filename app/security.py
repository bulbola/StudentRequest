from __future__ import annotations

from functools import wraps
from secrets import token_urlsafe
from html import escape
from flask import abort, request, session
from flask_login import current_user
from . import db
from .models import ActivityLog
from .services import add_notification

ROLE_NAMES = {
    'student': 'Студент',
    'employee': 'Сотрудник подразделения',
    'manager': 'Руководитель подразделения',
    'admin': 'Администратор системы',
}

ALLOWED_STATUSES = {'created', 'in_progress', 'needs_info', 'processed', 'closed', 'rejected'}
ALLOWED_PRIORITIES = {'low', 'normal', 'high'}
ALLOWED_FILE_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'}
ALLOWED_ROLES = set(ROLE_NAMES.keys())


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_csrf_token() -> str:
    token = session.get('_csrf_token')
    if not token:
        token = token_urlsafe(32)
        session['_csrf_token'] = token
    return token


def validate_csrf_token(token: str | None):
    if not token or token != session.get('_csrf_token'):
        abort(400, description='Некорректный CSRF-токен')


def sanitize_text(value: str | None, max_len: int | None = None) -> str:
    value = (value or '').strip()
    if max_len is not None:
        value = value[:max_len]
    return escape(value)


def is_allowed_file(filename: str) -> bool:
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_FILE_EXTENSIONS


def log_action(user_id: int | None, action: str, entity_type: str | None = None, entity_id: int | None = None):
    db.session.add(ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=request.headers.get('X-Forwarded-For', request.remote_addr) if request else 'system',
    ))


def notify_user(user_id: int, title: str, body: str, request_id: int | None = None, channel: str = 'internal'):
    add_notification(user_id, title, body, request_id, channel)
