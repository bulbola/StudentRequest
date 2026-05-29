from app import create_app, db
from app.models import User, StudentProfile, EmployeeProfile, RequestCategory, Request
from werkzeug.security import generate_password_hash
import click

app = create_app()

@app.cli.command('init-db')
def init_db():
    db.create_all()
    click.echo('Database initialized')

@app.cli.command('seed-db')
def seed_db():
    if not User.query.filter_by(email='admin@example.com').first():
        admin = User(full_name='Администратор системы', email='admin@example.com', role='admin', password_hash=generate_password_hash('admin123'))
        employee_user = User(full_name='Сотрудник подразделения', email='employee@example.com', role='employee', password_hash=generate_password_hash('employee123'))
        student_user = User(full_name='Иванов Иван Иванович', email='student@example.com', role='student', password_hash=generate_password_hash('student123'))
        db.session.add_all([admin, employee_user, student_user])
        db.session.flush()
        db.session.add(StudentProfile(user_id=student_user.id, group_name='ИС-401', course=4, direction='Информационные системы и технологии'))
        db.session.add(EmployeeProfile(user_id=employee_user.id, position='специалист', department='структурное подразделение Университета'))
        cats = [
            RequestCategory(name='Учебный процесс', description='Вопросы по расписанию, дисциплинам и консультациям'),
            RequestCategory(name='Практика', description='Вопросы по практике и отчетным документам'),
            RequestCategory(name='Документы', description='Запросы справок и иных документов'),
            RequestCategory(name='Техническая поддержка', description='Технические обращения по работе сервисов'),
        ]
        db.session.add_all(cats)
        db.session.flush()
        db.session.add(Request(student_id=student_user.id, category_id=cats[1].id, title='Уточнение по индивидуальному заданию', description='Прошу уточнить порядок загрузки индивидуального задания.', status='created', priority='normal'))
        db.session.commit()
    click.echo('Demo data created')

if __name__ == '__main__':
    app.run(debug=True)
