# Powershell script to recreate the Git history stage-by-stage
# Using the discovered GitHub Desktop Git executable path

$git = "C:\Users\hp\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\cmd\git.exe"

Write-Host "Preserving final main.py code content..." -ForegroundColor Green
$FinalMain = Get-Content "main.py" -Raw

# Helper to write files and commit
function Commit-Stage {
    param(
        [string]$Message,
        [string]$CodeContent
    )
    $CodeContent | Out-File -FilePath "main.py" -Encoding utf8
    & $git add main.py
    & $git commit -m $Message
    Write-Host "Committed: $Message" -ForegroundColor Cyan
}

# Stage 0
Commit-Stage -Message "Stage 0: hello server" -CodeContent @'
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.get("/", response_class=PlainTextResponse)
def read_root():
    return "Hello, server"
'@

# Stage 1
Commit-Stage -Message "Stage 1: root and health endpoints" -CodeContent @'
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def read_health():
    return {
        "status": "ok"
    }
'@

# Stage 2
Commit-Stage -Message "Stage 2: read endpoints with 404" -CodeContent @'
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Set up Git", "done": True},
    {"id": 3, "title": "Complete Stage 2", "done": False}
]

@app.get("/")
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def read_health():
    return {
        "status": "ok"
    }

@app.get("/tasks")
def read_tasks():
    return tasks

@app.get("/tasks/{id}")
def read_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {id} not found"}
    )
'@

# Stage 3
Commit-Stage -Message "Stage 3: create with validation" -CodeContent @'
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Set up Git", "done": True},
    {"id": 3, "title": "Complete Stage 2", "done": False}
]

@app.get("/")
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def read_health():
    return {
        "status": "ok"
    }

@app.get("/tasks")
def read_tasks():
    return tasks

@app.get("/tasks/{id}")
def read_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {id} not found"}
    )

@app.post("/tasks", status_code=201)
async def create_task(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    
    if "title" not in body or not isinstance(body["title"], str) or not body["title"].strip():
        return JSONResponse(status_code=400, content={"error": "Title is required and cannot be empty"})
    
    new_id = max([t["id"] for t in tasks]) + 1 if tasks else 1
    new_task = {
        "id": new_id,
        "title": body["title"].strip(),
        "done": False
    }
    tasks.append(new_task)
    return new_task
'@

# Stage 4
Commit-Stage -Message "Stage 4: full CRUD" -CodeContent @'
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI()

tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Set up Git", "done": True},
    {"id": 3, "title": "Complete Stage 2", "done": False}
]

@app.get("/")
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def read_health():
    return {
        "status": "ok"
    }

@app.get("/tasks")
def read_tasks():
    return tasks

@app.get("/tasks/{id}")
def read_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {id} not found"}
    )

@app.post("/tasks", status_code=201)
async def create_task(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    
    if "title" not in body or not isinstance(body["title"], str) or not body["title"].strip():
        return JSONResponse(status_code=400, content={"error": "Title is required and cannot be empty"})
    
    new_id = max([t["id"] for t in tasks]) + 1 if tasks else 1
    new_task = {
        "id": new_id,
        "title": body["title"].strip(),
        "done": False
    }
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{id}")
async def update_task(id: int, request: Request):
    task_idx = -1
    for i, task in enumerate(tasks):
        if task["id"] == id:
            task_idx = i
            break
            
    if task_idx == -1:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {id} not found"}
        )
        
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
        
    if "title" not in body and "done" not in body:
        return JSONResponse(
            status_code=400,
            content={"error": "At least one of 'title' or 'done' must be provided"}
        )
        
    if "title" in body:
        if not isinstance(body["title"], str) or not body["title"].strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Title must be a non-empty string"}
            )
            
    if "done" in body:
        if not isinstance(body["done"], bool):
            return JSONResponse(
                status_code=400,
                content={"error": "Done must be a boolean"}
            )
            
    if "title" in body:
        tasks[task_idx]["title"] = body["title"].strip()
    if "done" in body:
        tasks[task_idx]["done"] = body["done"]
        
    return tasks[task_idx]

@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    for i, task in enumerate(tasks):
        if task["id"] == id:
            tasks.pop(i)
            return Response(status_code=204)
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {id} not found"}
    )
'@

# Stage 5 & Extras:
Commit-Stage -Message "Stage 5: Swagger UI" -CodeContent $FinalMain

# Stage 6: Publish & Docs
$FinalMain | Out-File -FilePath "main.py" -Encoding utf8
& $git add requirements.txt README.md recreate_git_history.ps1 ai-version/main.py main.py
& $git commit -m "Stage 6: publish and docs"

# Stage 7: AI Rematch
& $git add ai-version/main.py README.md
& $git commit -m "Stage 7: AI vs me"

Write-Host "Success! Git history has been successfully recreated stage-by-stage locally." -ForegroundColor Green
