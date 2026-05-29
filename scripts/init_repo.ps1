param(
    [Parameter(Mandatory=$true)]
    [string]$RemoteUrl
)

# Скрипт запускается из корня проекта StudentRequest.
# Пример: powershell -ExecutionPolicy Bypass -File scripts/init_repo.ps1 https://github.com/USERNAME/StudentRequest.git

if (-Not (Test-Path ".git")) {
    git init
}

git branch -M main
git add .
git commit -m "Initial project structure for StudentRequest"
git remote remove origin 2>$null
git remote add origin $RemoteUrl
git push -u origin main

Write-Host "Готово. Дальше делайте небольшие содержательные коммиты по docs/commit_plan.md"
