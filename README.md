# StudentRequest

StudentRequest — веб-информационная система учета и обработки заявок студентов в структурном подразделении университета.

## Публичные ссылки

- GitHub: https://github.com/bulbola/StudentRequest
- Демо-сайт Render: https://studentrequest.onrender.com

## Основные возможности

- роли пользователей: студент, сотрудник, руководитель подразделения, администратор;
- создание и обработка заявок студентов;
- категории заявок и закрепление сотрудников за категориями;
- жизненный цикл статусов: создана, в работе, требуется уточнение, обработана, закрыта, отклонена;
- SLA, эскалация просроченных заявок и уведомления;
- блокировка заявки при обработке одним сотрудником;
- журнал действий activity_log;
- экспорт отчетов в XLSX;
- тесты pytest и покрытие coverage.

## Быстрый запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements-sqlite.txt
flask --app run.py init-db
flask --app run.py run
```

Для PostgreSQL задайте переменные окружения:

```bash
export SECRET_KEY="change-me"
export DATABASE_URL="postgresql://user:password@host:5432/student_request"
flask --app run.py db upgrade
```

## Демонстрационные учетные записи

- student@example.com / student123
- employee@example.com / employee123
- manager@example.com / manager123
- admin@example.com / admin123

## Тестирование

```bash
python -m pytest
coverage run -m pytest
coverage report -m
```
