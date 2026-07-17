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
