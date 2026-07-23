import os
import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# Load .env for local development
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:dev@localhost:5432/tasks")

def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=psycopg.rows.dict_row)

def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
            cur.execute("SELECT COUNT(*) AS count FROM tasks")
            row = cur.fetchone()
            if row["count"] == 0:
                cur.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                    [
                        ("Learn FastAPI", False),
                        ("Set up Git", True),
                        ("Complete Stage 2", False)
                    ]
                )
        conn.commit()

app = FastAPI(
    title="Task CRUD API (AI Version — PostgreSQL)",
    description="AI-generated PostgreSQL CRUD API for the internship assignment Stage 6 comparison.",
    version="3.0-ai"
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return {
        "name": "Task API (AI)",
        "version": "3.0-ai",
        "storage": "PostgreSQL (Docker)",
        "endpoints": ["/tasks", "/health"]
    }

@app.get("/health")
def read_health():
    return {"status": "ok"}

@app.get("/tasks")
def read_tasks():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks ORDER BY id ASC")
            rows = cur.fetchall()
    return [{"id": r["id"], "title": r["title"], "done": r["done"]} for r in rows]

@app.get("/tasks/{id}")
def read_task(id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks WHERE id = %s", (id,))
            row = cur.fetchone()
    if not row:
        return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})
    return {"id": row["id"], "title": row["title"], "done": row["done"]}

@app.post("/tasks", status_code=201)
async def create_task(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    if "title" not in body or not isinstance(body["title"], str) or not body["title"].strip():
        return JSONResponse(status_code=400, content={"error": "Title is required and cannot be empty"})
    title = body["title"].strip()
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, FALSE) RETURNING id, title, done",
                (title,)
            )
            row = cur.fetchone()
        conn.commit()
    return {"id": row["id"], "title": row["title"], "done": row["done"]}

@app.put("/tasks/{id}")
async def update_task(id: int, request: Request):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks WHERE id = %s", (id,))
            existing = cur.fetchone()
    if not existing:
        return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    if "title" not in body and "done" not in body:
        return JSONResponse(status_code=400, content={"error": "At least one of 'title' or 'done' must be provided"})
    new_title = existing["title"]
    new_done = existing["done"]
    if "title" in body:
        if not isinstance(body["title"], str) or not body["title"].strip():
            return JSONResponse(status_code=400, content={"error": "Title must be a non-empty string"})
        new_title = body["title"].strip()
    if "done" in body:
        if not isinstance(body["done"], bool):
            return JSONResponse(status_code=400, content={"error": "Done must be a boolean"})
        new_done = body["done"]
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done",
                (new_title, new_done, id)
            )
            row = cur.fetchone()
        conn.commit()
    return {"id": row["id"], "title": row["title"], "done": row["done"]}

@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (id,))
            deleted = cur.fetchone()
        if not deleted:
            return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})
        conn.commit()
    return Response(status_code=204)
