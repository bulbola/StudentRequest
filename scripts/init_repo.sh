#!/usr/bin/env bash
set -e

# Скрипт запускается из корня проекта StudentRequest.
# Перед запуском создайте пустой репозиторий на GitHub/GitFlic и укажите remote URL.
# Пример: ./scripts/init_repo.sh https://github.com/USERNAME/StudentRequest.git

REMOTE_URL="$1"

if [ -z "$REMOTE_URL" ]; then
  echo "Укажите URL удаленного репозитория: ./scripts/init_repo.sh <remote-url>"
  exit 1
fi

if [ ! -d .git ]; then
  git init
fi

git branch -M main
git add .
git commit -m "Initial project structure for StudentRequest"
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE_URL"
git push -u origin main

echo "Готово. Дальше делайте небольшие содержательные коммиты по docs/commit_plan.md"
