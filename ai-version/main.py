import sqlite3
from pathlib import Path
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

DB_PATH = Path(__file__).parent / "ai_tasks.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
        """)
        cursor.execute("SELECT COUNT(*) AS count FROM tasks")
        row = cursor.fetchone()
        if row["count"] == 0:
            cursor.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                [
                    ("Learn FastAPI", 0),
                    ("Set up Git", 1),
                    ("Complete Stage 2", 0)
                ]
            )
        conn.commit()

app = FastAPI(
    title="Task API (SQLite Migration)",
    description="A Python FastAPI To-Do list CRUD API using SQLite storage.",
    version="1.0"
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom exception handler to return 400 Bad Request for validation errors.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Bad Request: Invalid parameters or body format"}
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Custom exception handler for Starlette HTTPExceptions.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    """
    Retrieve metadata about the Task API, including name, version, and storage format.
    """
    return {
        "name": "Task API",
        "version": "1.0",
        "storage": "SQLite (ai_tasks.db)",
        "endpoints": ["/tasks", "/health"]
    }

@app.get("/health", status_code=status.HTTP_200_OK)
def read_health():
    """
    Check the health status of the API application.
    """
    return {"status": "ok"}

@app.get("/tasks", status_code=status.HTTP_200_OK)
def read_tasks():
    """
    Retrieve all tasks from the SQLite database.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done FROM tasks ORDER BY id ASC")
        rows = cursor.fetchall()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"])
        }
        for row in rows
    ]

@app.get("/tasks/{id}", status_code=status.HTTP_200_OK)
def read_task(id: int):
    """
    Retrieve a single task by ID from SQLite using a parameterized SQL query.
    Returns 404 Not Found if the task ID does not exist.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (id,))
        row = cursor.fetchone()

    if not row:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {id} not found"}
        )

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"])
    }

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(request: Request):
    """
    Create a new task in SQLite using a parameterized SQL query.
    Validates non-empty title (returns 400 Bad Request if missing or empty).
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid JSON body"}
        )

    if not isinstance(body, dict) or "title" not in body:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Title is required"}
        )

    title = body.get("title")
    if not isinstance(title, str) or not title.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Title cannot be empty"}
        )

    clean_title = title.strip()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (title, done) VALUES (?, 0)", (clean_title,))
        task_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"])
        }
    )

@app.put("/tasks/{id}", status_code=status.HTTP_200_OK)
async def update_task(id: int, request: Request):
    """
    Update title and/or done status of an existing task in SQLite using parameterized SQL.
    Returns 404 for unknown ID and 400 for invalid body.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (id,))
        existing = cursor.fetchone()

    if not existing:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {id} not found"}
        )

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid JSON body"}
        )

    if not isinstance(body, dict) or ("title" not in body and "done" not in body):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Request body must contain 'title' and/or 'done'"}
        )

    new_title = existing["title"]
    new_done = existing["done"]

    if "title" in body:
        title_val = body["title"]
        if not isinstance(title_val, str) or not title_val.strip():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Title must be a non-empty string"}
            )
        new_title = title_val.strip()

    if "done" in body:
        done_val = body["done"]
        if not isinstance(done_val, bool):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Done must be a boolean"}
            )
        new_done = 1 if done_val else 0

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (new_title, new_done, id)
        )
        conn.commit()

        cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (id,))
        row = cursor.fetchone()

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"])
    }

@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int):
    """
    Delete a task from SQLite by its unique ID.
    Returns status code 204 No Content upon successful deletion, or 404 Not Found if the ID does not exist.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tasks WHERE id = ?", (id,))
        existing = cursor.fetchone()

        if not existing:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Task {id} not found"}
            )

        cursor.execute("DELETE FROM tasks WHERE id = ?", (id,))
        conn.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
