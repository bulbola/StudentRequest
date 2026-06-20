# План развертывания StudentRequest

## 1. Локальная учебная версия SQLite

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements-sqlite.txt
export FLASK_APP=run.py
export SECRET_KEY="dev-secret"
flask init-db
flask seed-db
pytest
coverage run -m pytest
coverage report -m
flask run
```

## 2. Переключение на PostgreSQL

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=run.py
export SECRET_KEY="production-secret"
export DATABASE_URL="postgresql+psycopg://student_request:password@localhost:5432/student_request"
flask db upgrade
flask seed-db
```

В проекте используется `psycopg[binary]` 3.x вместо `psycopg2-binary`, так как он корректнее устанавливается на современных версиях Python, включая Python 3.13.

## 3. Миграции

Миграции подключены через Flask-Migrate/Alembic. Первый снимок схемы находится в каталоге `migrations/versions/`.

Команды сопровождения:

```bash
flask db migrate -m "change description"
flask db upgrade
flask db downgrade
```

`flask init-db` оставлен только для учебной SQLite-отладки и не должен использоваться как основной механизм промышленной миграции.

## 4. SLA и эскалация

Контроль просроченных заявок запускается командой:

```bash
flask check-sla
```

Для промышленной эксплуатации команду следует запускать по расписанию cron/systemd timer, например раз в 15-30 минут.

## 5. Проверка после развертывания

1. Открыть `/help` и убедиться, что справка содержит инструкцию.
2. Войти как студент и создать заявку.
3. Проверить, что сотрудник и руководитель получили внутреннее уведомление.
4. Войти как сотрудник, взять заявку в работу и убедиться, что повторная блокировка другим сотрудником возвращает HTTP 409.
5. Отклонить заявку с причиной и проверить повторную подачу студентом.
6. Запустить `pytest` и `coverage report -m`.
