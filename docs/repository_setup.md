# Подготовка Git-репозитория StudentRequest

## 1. Создание удаленного репозитория

Создать пустой репозиторий на GitHub или GitFlic с названием:

`StudentRequest`

Рекомендуемая видимость на время проверки: public или private с доступом для руководителя.

## 2. Первичная публикация проекта

Вариант для Windows PowerShell:

```powershell
cd StudentRequest
powershell -ExecutionPolicy Bypass -File scripts/init_repo.ps1 https://github.com/USERNAME/StudentRequest.git
```

Вариант для Linux/macOS/Git Bash:

```bash
cd StudentRequest
./scripts/init_repo.sh https://github.com/USERNAME/StudentRequest.git
```

## 3. Важное требование по коммитам

По требованиям к проекту нужно не менее 50 содержательных коммитов от имени студента в период прохождения практики и подготовки ВКР. Не нужно загружать проект одним большим коммитом в конце.

Рекомендуемый порядок работы:

1. Сделать первый коммит со скелетом проекта.
2. Дальше дорабатывать проект маленькими шагами.
3. Каждый коммит должен отражать понятное изменение: модель БД, маршрут, шаблон, тест, документация, исправление ошибки.
4. Использовать план из `docs/commit_plan.md`.

## 4. Примеры команд для ежедневной работы

```bash
git status
git add .
git commit -m "Add student request creation form"
git push
```

## 5. Что не нужно коммитить

Не добавлять в репозиторий:

- `.env`;
- локальную базу `instance/*.db`;
- файлы из `__pycache__`;
- загруженные пользователями файлы из `app/static/uploads/`;
- виртуальное окружение `.venv/`.

Это уже настроено в `.gitignore`.
