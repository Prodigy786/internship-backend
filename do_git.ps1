$git = "C:\Users\hp\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\cmd\git.exe"

# Save the final main.py content before we overwrite it for staging
$finalMain = Get-Content "main.py" -Raw -Encoding utf8

# ── Stage 0 ─────────────────────────────────────────────────────────────────
Set-Content -Path "main.py" -Encoding utf8 -Value @'
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.get("/", response_class=PlainTextResponse)
def read_root():
    return "Hello, server"
'@
& $git rm --cached server.py 2>$null
& $git add main.py requirements.txt .gitignore
& $git commit -m "Stage 0: hello server"

# ── Stage 1 ─────────────────────────────────────────────────────────────────
Set-Content -Path "main.py" -Encoding utf8 -Value @'
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def read_health():
    return {"status": "ok"}
'@
& $git add main.py
& $git commit -m "Stage 1: root and health endpoints"

# ── Stage 2 ─────────────────────────────────────────────────────────────────
Set-Content -Path "main.py" -Encoding utf8 -Value @'
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Set up Git",    "done": True},
    {"id": 3, "title": "Complete Stage 2", "done": False},
]

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def read_health():
    return {"status": "ok"}

@app.get("/tasks")
def read_tasks():
    return tasks

@app.get("/tasks/{id}")
def read_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})
'@
& $git add main.py
& $git commit -m "Stage 2: read endpoints with 404"

# ── Stage 3 ─────────────────────────────────────────────────────────────────
Set-Content -Path "main.py" -Encoding utf8 -Value @'
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Set up Git",    "done": True},
    {"id": 3, "title": "Complete Stage 2", "done": False},
]

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def read_health():
    return {"status": "ok"}

@app.get("/tasks")
def read_tasks():
    return tasks

@app.get("/tasks/{id}")
def read_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

@app.post("/tasks", status_code=201)
async def create_task(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    if "title" not in body or not isinstance(body["title"], str) or not body["title"].strip():
        return JSONResponse(status_code=400, content={"error": "Title is required and cannot be empty"})
    new_id = max(t["id"] for t in tasks) + 1 if tasks else 1
    new_task = {"id": new_id, "title": body["title"].strip(), "done": False}
    tasks.append(new_task)
    return new_task
'@
& $git add main.py
& $git commit -m "Stage 3: create with validation"

# ── Stage 4 ─────────────────────────────────────────────────────────────────
Set-Content -Path "main.py" -Encoding utf8 -Value @'
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI()

tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Set up Git",    "done": True},
    {"id": 3, "title": "Complete Stage 2", "done": False},
]

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def read_health():
    return {"status": "ok"}

@app.get("/tasks")
def read_tasks():
    return tasks

@app.get("/tasks/{id}")
def read_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

@app.post("/tasks", status_code=201)
async def create_task(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    if "title" not in body or not isinstance(body["title"], str) or not body["title"].strip():
        return JSONResponse(status_code=400, content={"error": "Title is required and cannot be empty"})
    new_id = max(t["id"] for t in tasks) + 1 if tasks else 1
    new_task = {"id": new_id, "title": body["title"].strip(), "done": False}
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{id}")
async def update_task(id: int, request: Request):
    idx = next((i for i, t in enumerate(tasks) if t["id"] == id), -1)
    if idx == -1:
        return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    if "title" not in body and "done" not in body:
        return JSONResponse(status_code=400, content={"error": "At least one of title or done must be provided"})
    if "title" in body:
        if not isinstance(body["title"], str) or not body["title"].strip():
            return JSONResponse(status_code=400, content={"error": "Title must be a non-empty string"})
        tasks[idx]["title"] = body["title"].strip()
    if "done" in body:
        if not isinstance(body["done"], bool):
            return JSONResponse(status_code=400, content={"error": "Done must be a boolean"})
        tasks[idx]["done"] = body["done"]
    return tasks[idx]

@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    for i, task in enumerate(tasks):
        if task["id"] == id:
            tasks.pop(i)
            return Response(status_code=204)
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})
'@
& $git add main.py
& $git commit -m "Stage 4: full CRUD"

# ── Stage 5 — Swagger docstrings + Extras ───────────────────────────────────
Set-Content -Path "main.py" -Encoding utf8 -Value $finalMain
& $git add main.py
& $git commit -m "Stage 5: Swagger UI"

# ── Stage 6 — README + supporting files ────────────────────────────────────
& $git add README.md recreate_git_history.ps1 do_git.ps1
& $git commit -m "Stage 6: publish and docs"

# ── Stage 7 — AI rematch ────────────────────────────────────────────────────
& $git add ai-version/
& $git commit -m "Stage 7: AI vs me"

# ── Push ────────────────────────────────────────────────────────────────────
Write-Host "Pushing to GitHub..." -ForegroundColor Green
& $git push origin main

Write-Host "All done! Check https://github.com/Prodigy786/internship-backend" -ForegroundColor Cyan
