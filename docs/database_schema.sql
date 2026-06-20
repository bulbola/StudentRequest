-- StudentRequest database schema, generated from SQLAlchemy models.
-- SQLite is used for local учебная отладка; PostgreSQL is used in deployment via DATABASE_URL.

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    full_name VARCHAR(180) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    is_active_flag BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP
);
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_role ON users(role);

CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    group_name VARCHAR(30) NOT NULL,
    course INTEGER NOT NULL,
    direction VARCHAR(180) NOT NULL
);

CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    position VARCHAR(120) NOT NULL,
    department VARCHAR(180) NOT NULL,
    can_process_all BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE request_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);
CREATE INDEX ix_request_categories_is_active ON request_categories(is_active);

CREATE TABLE employee_categories (
    employee_id INTEGER NOT NULL REFERENCES users(id),
    category_id INTEGER NOT NULL REFERENCES request_categories(id),
    assigned_at TIMESTAMP,
    PRIMARY KEY (employee_id, category_id)
);

CREATE TABLE requests (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id),
    category_id INTEGER NOT NULL REFERENCES request_categories(id),
    assigned_employee_id INTEGER REFERENCES users(id),
    locked_by_id INTEGER REFERENCES users(id),
    locked_at TIMESTAMP,
    title VARCHAR(180) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(40),
    priority VARCHAR(30),
    sla_due_at TIMESTAMP,
    escalated_at TIMESTAMP,
    rejected_reason VARCHAR(500),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
CREATE INDEX ix_requests_student_id ON requests(student_id);
CREATE INDEX ix_requests_category_id ON requests(category_id);
CREATE INDEX ix_requests_assigned_employee_id ON requests(assigned_employee_id);
CREATE INDEX ix_requests_locked_by_id ON requests(locked_by_id);
CREATE INDEX ix_requests_status ON requests(status);
CREATE INDEX ix_requests_priority ON requests(priority);
CREATE INDEX ix_requests_sla_due_at ON requests(sla_due_at);
CREATE INDEX ix_requests_created_at ON requests(created_at);

CREATE TABLE request_files (
    id INTEGER PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES requests(id),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP
);
CREATE INDEX ix_request_files_request_id ON request_files(request_id);

CREATE TABLE request_comments (
    id INTEGER PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES requests(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP
);
CREATE INDEX ix_request_comments_request_id ON request_comments(request_id);

CREATE TABLE status_history (
    id INTEGER PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES requests(id),
    old_status VARCHAR(40),
    new_status VARCHAR(40) NOT NULL,
    changed_by INTEGER NOT NULL REFERENCES users(id),
    change_reason VARCHAR(500),
    changed_at TIMESTAMP
);
CREATE INDEX ix_status_history_request_id ON status_history(request_id);

CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(80),
    entity_id INTEGER,
    ip_address VARCHAR(64),
    created_at TIMESTAMP
);
CREATE INDEX ix_activity_log_user_id ON activity_log(user_id);
CREATE INDEX ix_activity_log_entity_id ON activity_log(entity_id);
CREATE INDEX ix_activity_log_created_at ON activity_log(created_at);

CREATE TABLE notifications (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    request_id INTEGER REFERENCES requests(id),
    channel VARCHAR(20) NOT NULL DEFAULT 'internal',
    title VARCHAR(180) NOT NULL,
    body VARCHAR(1000) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);
CREATE INDEX ix_notifications_user_id ON notifications(user_id);
CREATE INDEX ix_notifications_request_id ON notifications(request_id);
CREATE INDEX ix_notifications_is_read ON notifications(is_read);
