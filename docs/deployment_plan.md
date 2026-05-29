# План развертывания StudentRequest

1. Установить Python 3.11+.
2. Создать виртуальное окружение: `python -m venv .venv`.
3. Активировать окружение.
4. Установить зависимости: `pip install -r requirements.txt`.
5. Настроить переменные окружения SECRET_KEY и DATABASE_URL.
6. Инициализировать БД: `flask --app run.py init-db`.
7. Создать демонстрационные данные: `flask --app run.py seed-db`.
8. Запустить локально: `flask --app run.py run`.
9. Проверить вход под ролями student, employee, admin.
10. Проверить создание заявки, смену статуса и экспорт XLSX.
11. Для размещения использовать PythonAnywhere/Render и gunicorn.
