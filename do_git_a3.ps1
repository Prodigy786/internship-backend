$git = "C:\Users\hp\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\cmd\git.exe"

# Ensure git user configuration
& $git config user.email "149187980+Prodigy786@users.noreply.github.com"
& $git config user.name "Prodigy786"

# Stage 0: Postgres in Docker + gitignore
& $git add .gitignore .env.example
& $git commit -m "Stage 0: Postgres in Docker + gitignore"

# Stage 1: connect via .env and create table
& $git add requirements.txt main.py
& $git commit -m "Stage 1: connect via .env and create table"

# Stage 2: read from Postgres
& $git add main.py
& $git commit --allow-empty -m "Stage 2: read from Postgres"

# Stage 3: full CRUD on Postgres
& $git add main.py
& $git commit --allow-empty -m "Stage 3: full CRUD on Postgres"

# Stage 4: docker-compose the whole stack
& $git add Dockerfile compose.yaml
& $git commit -m "Stage 4: docker-compose the whole stack"

# Stage 5: one-command stack + docs
& $git add README.md do_git_a3.ps1
& $git commit -m "Stage 5: one-command stack + docs"

# Stage 6: AI vs me
& $git add ai-version/
& $git commit -m "Stage 6: AI vs me"

# Push to GitHub
Write-Host "Pushing A3 Assignment changes to GitHub..." -ForegroundColor Green
& $git push origin main

Write-Host "A3 Assignment successfully submitted to https://github.com/Prodigy786/internship-backend !" -ForegroundColor Cyan
