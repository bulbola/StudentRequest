from datetime import datetime, timedelta

from app import create_app, db
from app.models import (
    User, StudentProfile, EmployeeProfile, EmployeeCategory, RequestCategory,
    Request, ActivityLog, Notification, StatusHistory
)
from app.services import escalate_overdue_requests
from werkzeug.security import generate_password_hash


def make_app():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'SECRET_KEY': 'test-key'})
    with app.app_context():
        db.create_all()
        student = User(full_name='Студент', email='student@example.com', role='student', password_hash=generate_password_hash('student123'))
        admin = User(full_name='Админ', email='admin@example.com', role='admin', password_hash=generate_password_hash('admin123456'))
        manager = User(full_name='Руководитель', email='manager@example.com', role='manager', password_hash=generate_password_hash('manager123'))
        employee = User(full_name='Сотрудник', email='employee@example.com', role='employee', password_hash=generate_password_hash('employee123'))
        employee2 = User(full_name='Сотрудник 2', email='employee2@example.com', role='employee', password_hash=generate_password_hash('employee234'))
        category = RequestCategory(name='Практика', description='Практика')
        other_category = RequestCategory(name='Документы', description='Документы')
        db.session.add_all([student, admin, manager, employee, employee2, category, other_category])
        db.session.flush()
        db.session.add(StudentProfile(user_id=student.id, group_name='БИ-401', course=4, direction='Бизнес-информатика'))
        db.session.add(EmployeeProfile(user_id=employee.id, position='специалист', department='отдел', can_process_all=False))
        db.session.add(EmployeeProfile(user_id=employee2.id, position='специалист', department='отдел', can_process_all=True))
        db.session.add(EmployeeCategory(employee_id=employee.id, category_id=category.id))
        req = Request(
            student_id=student.id,
            category_id=category.id,
            title='Проверочная заявка',
            description='Длинное описание заявки для функционального теста.',
            priority='normal',
            status='created',
            sla_due_at=datetime.utcnow() + timedelta(hours=48),
        )
        db.session.add(req)
        db.session.flush()
        db.session.add(StatusHistory(request_id=req.id, old_status=None, new_status='created', changed_by=student.id))
        db.session.commit()
    return app


def csrf(client, url='/login'):
    client.get(url)
    with client.session_transaction() as sess:
        return sess.get('_csrf_token')


def login(client, email, password):
    token = csrf(client, '/login')
    return client.post('/login', data={'email': email, 'password': password, '_csrf_token': token}, follow_redirects=False)


def test_app_factory():
    assert make_app() is not None


def test_student_forbidden_admin_returns_403():
    app = make_app()
    client = app.test_client()
    login(client, 'student@example.com', 'student123')
    resp = client.get('/admin/')
    assert resp.status_code == 403


def test_help_page_has_real_instruction():
    app = make_app()
    client = app.test_client()
    resp = client.get('/help')
    assert resp.status_code == 200
    assert 'Повторная подача'.encode('utf-8') in resp.data
    assert 'SLA'.encode('utf-8') in resp.data


def test_create_request_validation_rejects_short_description():
    app = make_app()
    client = app.test_client()
    login(client, 'student@example.com', 'student123')
    token = csrf(client, '/student/requests/create')
    with app.app_context():
        category = RequestCategory.query.filter_by(name='Практика').first()
    resp = client.post('/student/requests/create', data={
        '_csrf_token': token,
        'category_id': str(category.id),
        'title': 'Нормальная тема',
        'description': 'коротко',
        'priority': 'normal',
    })
    assert resp.status_code == 400


def test_create_request_adds_history_log_and_notifications():
    app = make_app()
    client = app.test_client()
    login(client, 'student@example.com', 'student123')
    token = csrf(client, '/student/requests/create')
    with app.app_context():
        category = RequestCategory.query.filter_by(name='Практика').first()
        before = Request.query.count()
    resp = client.post('/student/requests/create', data={
        '_csrf_token': token,
        'category_id': str(category.id),
        'title': 'Заявка по практике',
        'description': 'Прошу проверить комплект документов по практике перед загрузкой.',
        'priority': 'high',
    }, follow_redirects=False)
    assert resp.status_code == 302
    with app.app_context():
        assert Request.query.count() == before + 1
        req = Request.query.order_by(Request.id.desc()).first()
        assert req.sla_due_at is not None
        assert StatusHistory.query.filter_by(request_id=req.id, new_status='created').count() == 1
        assert ActivityLog.query.filter_by(action='create_request', entity_id=req.id).count() == 1
        # уведомлены закрепленный сотрудник, сотрудник общей очереди и руководитель
        assert Notification.query.filter_by(request_id=req.id).count() >= 3


def test_employee_category_restriction():
    app = make_app()
    client = app.test_client()
    login(client, 'employee@example.com', 'employee123')
    with app.app_context():
        student = User.query.filter_by(role='student').first()
        other_category = RequestCategory.query.filter_by(name='Документы').first()
        req = Request(student_id=student.id, category_id=other_category.id, title='Другая категория', description='Описание другой категории длиной больше двадцати символов.', status='created')
        db.session.add(req)
        db.session.commit()
        rid = req.id
    resp = client.get(f'/employee/requests/{rid}')
    assert resp.status_code == 403


def test_atomic_take_request_returns_409_when_locked_by_other_employee():
    app = make_app()
    client1 = app.test_client()
    client2 = app.test_client()
    with app.app_context():
        req_id = Request.query.first().id
    login(client1, 'employee@example.com', 'employee123')
    token1 = csrf(client1, f'/employee/requests/{req_id}')
    resp1 = client1.post(f'/employee/requests/{req_id}/take', data={'_csrf_token': token1})
    assert resp1.status_code == 302
    login(client2, 'employee2@example.com', 'employee234')
    token2 = csrf(client2, f'/employee/requests/{req_id}')
    resp2 = client2.post(f'/employee/requests/{req_id}/take', data={'_csrf_token': token2})
    assert resp2.status_code == 409


def test_processing_requires_lock():
    app = make_app()
    client = app.test_client()
    with app.app_context():
        req_id = Request.query.first().id
    login(client, 'employee@example.com', 'employee123')
    token = csrf(client, f'/employee/requests/{req_id}')
    resp = client.post(f'/employee/requests/{req_id}', data={'_csrf_token': token, 'status': 'closed', 'comment_text': 'готово'})
    assert resp.status_code == 409


def test_reject_requires_reason_then_allows_resubmit():
    app = make_app()
    client = app.test_client()
    with app.app_context():
        req_id = Request.query.first().id
    login(client, 'employee@example.com', 'employee123')
    token = csrf(client, f'/employee/requests/{req_id}')
    client.post(f'/employee/requests/{req_id}/take', data={'_csrf_token': token})
    token = csrf(client, f'/employee/requests/{req_id}')
    resp = client.post(f'/employee/requests/{req_id}', data={'_csrf_token': token, 'status': 'rejected', 'rejected_reason': ''})
    assert resp.status_code == 302
    with app.app_context():
        assert db.session.get(Request, req_id).status == 'in_progress'
    token = csrf(client, f'/employee/requests/{req_id}')
    resp = client.post(f'/employee/requests/{req_id}', data={'_csrf_token': token, 'status': 'rejected', 'rejected_reason': 'Недостаточно данных'})
    assert resp.status_code == 302
    with app.app_context():
        assert db.session.get(Request, req_id).status == 'rejected'
    client = app.test_client()
    login(client, 'student@example.com', 'student123')
    token = csrf(client, f'/student/requests/{req_id}')
    resp = client.post(f'/student/requests/{req_id}/resubmit', data={'_csrf_token': token, 'comment_text': 'Добавил сведения'})
    assert resp.status_code == 302
    with app.app_context():
        req = db.session.get(Request, req_id)
        assert req.status == 'created'
        assert req.rejected_reason is None


def test_manager_stats_allowed_without_admin_rights():
    app = make_app()
    client = app.test_client()
    login(client, 'manager@example.com', 'manager123')
    assert client.get('/employee/stats').status_code == 200
    assert client.get('/admin/').status_code == 403


def test_admin_can_create_category_and_user():
    app = make_app()
    client = app.test_client()
    login(client, 'admin@example.com', 'admin123456')
    token = csrf(client, '/admin/categories/new')
    resp = client.post('/admin/categories/new', data={'_csrf_token': token, 'name': 'Консультации', 'description': 'Запись на консультации', 'is_active': 'on'})
    assert resp.status_code == 302
    token = csrf(client, '/admin/users/new')
    resp = client.post('/admin/users/new', data={
        '_csrf_token': token,
        'full_name': 'Новый сотрудник',
        'email': 'new.employee@example.com',
        'role': 'employee',
        'password': 'employee999',
        'position': 'специалист',
        'department': 'отдел',
        'can_process_all': 'on',
        'is_active_flag': 'on',
    })
    assert resp.status_code == 302
    with app.app_context():
        assert RequestCategory.query.filter_by(name='Консультации').count() == 1
        assert User.query.filter_by(email='new.employee@example.com').count() == 1


def test_csrf_missing_is_rejected():
    app = make_app()
    client = app.test_client()
    login(client, 'student@example.com', 'student123')
    with app.app_context():
        category = RequestCategory.query.filter_by(name='Практика').first()
    resp = client.post('/student/requests/create', data={
        'category_id': str(category.id),
        'title': 'Заявка без токена',
        'description': 'Описание заявки без csrf токена для проверки защиты.',
        'priority': 'normal',
    })
    assert resp.status_code == 400


def test_sla_checker_escalates_overdue_request():
    app = make_app()
    with app.app_context():
        req = Request.query.first()
        req.sla_due_at = datetime.utcnow() - timedelta(hours=1)
        db.session.commit()
        count = escalate_overdue_requests()
        assert count == 1
        assert db.session.get(Request, req.id).escalated_at is not None
        assert ActivityLog.query.filter_by(action='auto_escalate_sla', entity_id=req.id).count() == 1
        assert Notification.query.filter_by(request_id=req.id).count() >= 2


def test_activity_log_model_available():
    app = make_app()
    with app.app_context():
        assert ActivityLog.query.count() == 0
