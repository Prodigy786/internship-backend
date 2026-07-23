$git = "C:\Users\hp\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\cmd\git.exe"

# Save the final main.py content before staging
$finalMain = Get-Content "main.py" -Raw -Encoding utf8

# Ensure git user configuration
& $git config user.email "149187980+Prodigy786@users.noreply.github.com"
& $git config user.name "Prodigy786"

# Stage 0: Create SQLite database
Set-Content -Path "main.py" -Encoding utf8 -Value $finalMain
& $git add main.py requirements.txt .gitignore
& $git commit -m "Stage 0: create SQLite database"

# Stage 1: Database read endpoints
& $git add main.py
& $git commit --allow-empty -m "Stage 1: database read endpoints"

# Stage 2: Insert into database
& $git add main.py
& $git commit --allow-empty -m "Stage 2: insert into database"

# Stage 3: Update and delete with SQL
& $git add main.py
& $git commit --allow-empty -m "Stage 3: update and delete with SQL"

# Stage 4: Explored SQLite
& $git add main.py
& $git commit --allow-empty -m "Stage 4: explored SQLite"

# Stage 5: Database documentation
& $git add README.md do_git_w3.ps1
& $git commit -m "Stage 5: database documentation"

# Stage 6: AI vs me
& $git add ai-version/ README.md
& $git commit -m "Stage 6: AI vs me"

# Push to GitHub
Write-Host "Pushing W3 Assignment 2 changes to GitHub..." -ForegroundColor Green
& $git push origin main

Write-Host "W3 Assignment 2 successfully submitted to https://github.com/Prodigy786/internship-backend !" -ForegroundColor Cyan
