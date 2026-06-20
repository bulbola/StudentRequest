from datetime import datetime
from . import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(180), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    # student, employee, manager, admin
    role = db.Column(db.String(20), nullable=False, default='student', index=True)
    is_active_flag = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_active(self):
        return self.is_active_flag


class StudentProfile(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    group_name = db.Column(db.String(30), nullable=False)
    course = db.Column(db.Integer, nullable=False)
    direction = db.Column(db.String(180), nullable=False)
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))


class EmployeeProfile(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    position = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(180), nullable=False)
    can_process_all = db.Column(db.Boolean, default=False, nullable=False)
    user = db.relationship('User', backref=db.backref('employee_profile', uselist=False))


class RequestCategory(db.Model):
    __tablename__ = 'request_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)


class EmployeeCategory(db.Model):
    __tablename__ = 'employee_categories'
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('request_categories.id'), primary_key=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    employee = db.relationship('User', backref='employee_categories')
    category = db.relationship('RequestCategory')


class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('request_categories.id'), nullable=False, index=True)
    assigned_employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    locked_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    locked_at = db.Column(db.DateTime, nullable=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(40), default='created', index=True)
    priority = db.Column(db.String(30), default='normal', index=True)
    sla_due_at = db.Column(db.DateTime, nullable=True, index=True)
    escalated_at = db.Column(db.DateTime, nullable=True)
    rejected_reason = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship('User', foreign_keys=[student_id])
    category = db.relationship('RequestCategory')
    assigned_employee = db.relationship('User', foreign_keys=[assigned_employee_id])
    locked_by = db.relationship('User', foreign_keys=[locked_by_id])


class RequestFile(db.Model):
    __tablename__ = 'request_files'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    request = db.relationship('Request', backref='files')


class RequestComment(db.Model):
    __tablename__ = 'request_comments'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')
    request = db.relationship('Request', backref='comments')


class StatusHistory(db.Model):
    __tablename__ = 'status_history'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False, index=True)
    old_status = db.Column(db.String(40), nullable=True)
    new_status = db.Column(db.String(40), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    change_reason = db.Column(db.String(500), nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    request = db.relationship('Request', backref='status_history')


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(255), nullable=False)
    entity_type = db.Column(db.String(80), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    ip_address = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user = db.relationship('User')


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=True, index=True)
    channel = db.Column(db.String(20), nullable=False, default='internal')
    title = db.Column(db.String(180), nullable=False)
    body = db.Column(db.String(1000), nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')
    request = db.relationship('Request')
