КАК ОБНОВИТЬ СТАРЫЙ GITHUB-РЕПОЗИТОРИЙ

1. Распакуйте содержимое этого архива прямо в корень старой папки репозитория StudentRequest, где уже есть папка .git.
   Важно: не удаляйте папку .git и не делайте git init заново.

2. После копирования откройте терминал в корне репозитория и выполните:

   git status
   py -m pytest
   coverage run -m pytest
   coverage report -m

3. Если тесты прошли, добавьте изменения:

   git add .
   git commit -m "feat: add practice report improvements"
   git push

4. Проверка результата:

   git status
   git rev-list --count HEAD

После push старая история коммитов сохранится, а новая версия будет добавлена поверх нее.
