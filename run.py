from app import create_app, db
from app.models import User, StudentProfile, EmployeeProfile, RequestCategory, Request, EmployeeCategory, StatusHistory
from app.services import escalate_overdue_requests
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import click

app = create_app()


@app.cli.command('init-db')
def init_db():
    db.create_all()
    click.echo('Database initialized. For production use: flask db upgrade')


@app.cli.command('seed-db')
def seed_db():
    if not User.query.filter_by(email='admin@example.com').first():
        admin = User(full_name='Администратор системы', email='admin@example.com', role='admin', password_hash=generate_password_hash('admin123'))
        manager = User(full_name='Руководитель подразделения', email='manager@example.com', role='manager', password_hash=generate_password_hash('manager123'))
        employee_any = User(full_name='Сотрудник общей очереди', email='employee@example.com', role='employee', password_hash=generate_password_hash('employee123'))
        employee_practice = User(full_name='Специалист по практике', email='practice@example.com', role='employee', password_hash=generate_password_hash('practice123'))
        student_user = User(full_name='Иванов Иван Иванович', email='student@example.com', role='student', password_hash=generate_password_hash('student123'))
        db.session.add_all([admin, manager, employee_any, employee_practice, student_user])
        db.session.flush()
        db.session.add(StudentProfile(user_id=student_user.id, group_name='ИС-401', course=4, direction='Бизнес-информатика'))
        db.session.add(EmployeeProfile(user_id=employee_any.id, position='специалист', department='структурное подразделение Университета', can_process_all=True))
        db.session.add(EmployeeProfile(user_id=employee_practice.id, position='специалист по практике', department='структурное подразделение Университета', can_process_all=False))
        cats = [
            RequestCategory(name='Учебный процесс', description='Вопросы по расписанию, дисциплинам и консультациям'),
            RequestCategory(name='Практика', description='Вопросы по практике и отчетным документам'),
            RequestCategory(name='Документы', description='Запросы справок и иных документов'),
            RequestCategory(name='Техническая поддержка', description='Технические обращения по работе сервисов'),
        ]
        db.session.add_all(cats)
        db.session.flush()
        db.session.add(EmployeeCategory(employee_id=employee_practice.id, category_id=cats[1].id))
        demo_request = Request(
            student_id=student_user.id,
            category_id=cats[1].id,
            title='Уточнение по индивидуальному заданию',
            description='Прошу уточнить порядок загрузки индивидуального задания по практике.',
            status='created',
            priority='normal',
            sla_due_at=datetime.utcnow() + timedelta(hours=48),
        )
        db.session.add(demo_request)
        db.session.flush()
        db.session.add(StatusHistory(request_id=demo_request.id, old_status=None, new_status='created', changed_by=student_user.id))
        db.session.commit()
    click.echo('Demo data created')


@app.cli.command('check-sla')
def check_sla():
    """Запускает контроль SLA и эскалацию просроченных заявок."""
    count = escalate_overdue_requests(actor_user_id=None)
    click.echo(f'Escalated overdue requests: {count}')


if __name__ == '__main__':
    app.run(debug=True)
