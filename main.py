import os
import psycopg
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# Load .env file if present (local development)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    """Open a new psycopg connection using DATABASE_URL."""
    return psycopg.connect(DATABASE_URL, row_factory=psycopg.rows.dict_row)

def init_db():
    """Create the tasks table if missing and seed 3 default tasks when empty."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    title="Task CRUD API (PostgreSQL Edition)",
    description="A To-Do list CRUD API backed by a persistent PostgreSQL database running in Docker.",
    version="3.0"
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    """
    Get API metadata and endpoints list.
    """
    return {
        "name": "Task API",
        "version": "3.0",
        "storage": "PostgreSQL (Docker)",
        "endpoints": ["/tasks", "/stats", "/reset", "/health"]
    }

@app.get("/health")
def read_health():
    """
    Health check endpoint returning server status.
    """
    return {"status": "ok"}

@app.get("/tasks")
def read_tasks(done: bool | None = None, search: str | None = None):
    """
    Retrieve all tasks from PostgreSQL.
    Supports status filtering (?done=true/false) and ILIKE searching (?search=query).
    """
    query = "SELECT id, title, done, created_at, updated_at FROM tasks"
    params = []
    conditions = []

    if done is not None:
        conditions.append("done = %s")
        params.append(done)

    if search is not None and search.strip():
        conditions.append("title ILIKE %s")
        params.append(f"%{search.strip()}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY title ASC"

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "done": row["done"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
        for row in rows
    ]

@app.get("/tasks/{id}")
def read_task(id: int):
    """
    Retrieve a single task by ID from PostgreSQL using a parameterized query.
    Returns 404 if the task ID does not exist.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = %s",
                (id,)
            )
            row = cur.fetchone()

    if not row:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {id} not found"}
        )

    return {
        "id": row["id"],
        "title": row["title"],
        "done": row["done"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

@app.post("/tasks", status_code=201)
async def create_task(request: Request):
    """
    Create a new task in PostgreSQL.
    Validates that title is a non-empty string (returns 400 Bad Request if missing/empty).
    Uses RETURNING to fetch the newly created row in a single query.
    """
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
                "INSERT INTO tasks (title, done) VALUES (%s, FALSE) RETURNING id, title, done, created_at, updated_at",
                (title,)
            )
            row = cur.fetchone()
        conn.commit()

    return {
        "id": row["id"],
        "title": row["title"],
        "done": row["done"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

@app.put("/tasks/{id}")
async def update_task(id: int, request: Request):
    """
    Update a task's title and/or done status in PostgreSQL using parameterized SQL.
    Returns 404 for unknown ID and 400 for invalid body.
    Uses RETURNING to fetch the updated row in a single round-trip.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks WHERE id = %s", (id,))
            existing = cur.fetchone()

    if not existing:
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

    new_title = existing["title"]
    new_done = existing["done"]

    if "title" in body:
        if not isinstance(body["title"], str) or not body["title"].strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Title must be a non-empty string"}
            )
        new_title = body["title"].strip()

    if "done" in body:
        if not isinstance(body["done"], bool):
            return JSONResponse(
                status_code=400,
                content={"error": "Done must be a boolean"}
            )
        new_done = body["done"]

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE tasks
                SET title = %s, done = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, title, done, created_at, updated_at
                """,
                (new_title, new_done, id)
            )
            row = cur.fetchone()
        conn.commit()

    return {
        "id": row["id"],
        "title": row["title"],
        "done": row["done"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    """
    Remove a task from PostgreSQL by ID.
    Returns 204 No Content on success, and 404 if the task ID does not exist.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (id,))
            deleted = cur.fetchone()

        if not deleted:
            return JSONResponse(
                status_code=404,
                content={"error": f"Task {id} not found"}
            )
        conn.commit()

    return Response(status_code=204)

@app.get("/stats")
def get_stats():
    """
    Calculate task statistics directly in SQL using COUNT(*) and SUM.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN done IS TRUE THEN 1 ELSE 0 END) AS done_count
                FROM tasks
            """)
            row = cur.fetchone()

    total = row["total"] or 0
    done_count = row["done_count"] or 0
    open_count = total - done_count

    return {
        "total": total,
        "done": done_count,
        "open": open_count
    }

@app.post("/reset")
def reset_tasks():
    """
    Reset endpoint that clears the tasks table and re-seeds the 3 initial tasks
    inside a single transaction. Uses TRUNCATE ... RESTART IDENTITY for clean IDs.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE tasks RESTART IDENTITY")
            cur.executemany(
                "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                [
                    ("Learn FastAPI", False),
                    ("Set up Git", True),
                    ("Complete Stage 2", False)
                ]
            )
        conn.commit()

    return {"status": "success", "message": "PostgreSQL database reset to initial 3 seed tasks"}

