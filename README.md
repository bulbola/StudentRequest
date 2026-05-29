# StudentRequest

**StudentRequest** — учебная веб-информационная система учета и обработки заявок студентов в структурном подразделении Университета.

Проект подготовлен для преддипломной практики по теме:

> Разработка веб-информационной системы учета и обработки заявок студентов в структурном подразделении Университета

## Основные возможности

- авторизация пользователей;
- три роли: студент, сотрудник подразделения, администратор;
- личный кабинет студента;
- создание и просмотр заявок;
- выбор категории и приоритета заявки;
- прикрепление файла к заявке;
- панель сотрудника для обработки заявок;
- комментарии и изменение статусов;
- административная панель;
- просмотр пользователей и категорий;
- экспорт списка заявок в `.xlsx`;
- справка по системе.

## Технологии

- Python 3.11+
- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite для локального запуска
- PostgreSQL для целевого развертывания
- Jinja2
- HTML/CSS
- openpyxl
- pytest

## Быстрый запуск

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app run.py init-db
flask --app run.py seed-db
flask --app run.py run
```

После запуска открыть:

```text
http://127.0.0.1:5000
```

## Демо-учетные записи

| Роль | Email | Пароль |
|---|---|---|
| Администратор | admin@example.com | admin123 |
| Сотрудник | employee@example.com | employee123 |
| Студент | student@example.com | student123 |

## Тесты

```bash
pip install pytest
pytest -q
```

## Документация

Документы находятся в каталоге `docs`:

- `repository_setup.md` — инструкция по подготовке Git-репозитория;
- `commit_plan.md` — план 50 содержательных коммитов;
- `database_schema.sql` — схема базы данных;
- `deployment_plan.md` — план развертывания;
- `requirements_traceability.md` — матрица соответствия требованиям;
- `test_plan.md` — тест-план;
- `user_manual.md` — инструкция пользователя.

## Подготовка Git-репозитория

Создать пустой репозиторий на GitHub или GitFlic, затем выполнить:

```bash
./scripts/init_repo.sh https://github.com/USERNAME/StudentRequest.git
```

Для Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/init_repo.ps1 https://github.com/USERNAME/StudentRequest.git
```

Дальше вести разработку маленькими коммитами по плану из `docs/commit_plan.md`.

## Примечание

Проект является стартовой учебной версией. Для сдачи нужно постепенно доработать функционал, вести историю Git-коммитов и обновлять отчетные материалы.
