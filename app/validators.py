import re
from .security import ALLOWED_PRIORITIES, is_allowed_file

EMAIL_RE = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')


def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.fullmatch((email or '').strip()))


def validate_request_form(form, file_storage=None):
    errors = []
    title = (form.get('title') or '').strip()
    description = (form.get('description') or '').strip()
    category_id = (form.get('category_id') or '').strip()
    priority = (form.get('priority') or 'normal').strip()

    if not category_id.isdigit():
        errors.append('Не выбрана категория заявки.')
    if not (5 <= len(title) <= 180):
        errors.append('Тема заявки должна содержать от 5 до 180 символов.')
    if not (20 <= len(description) <= 4000):
        errors.append('Описание заявки должно содержать от 20 до 4000 символов.')
    if priority not in ALLOWED_PRIORITIES:
        errors.append('Указан некорректный приоритет заявки.')
    if file_storage and file_storage.filename and not is_allowed_file(file_storage.filename):
        errors.append('Недопустимый тип файла. Разрешены PDF, DOC/DOCX, XLS/XLSX, PNG, JPG/JPEG.')
    return errors
