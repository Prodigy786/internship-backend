import sqlite3
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

DB_PATH = Path("tasks.db")

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
                done INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    title="Task CRUD API (SQLite)",
    description="A To-Do list CRUD API backed by a persistent SQLite database.",
    version="2.0"
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
        "version": "2.0",
        "storage": "SQLite (tasks.db)",
        "endpoints": ["/tasks", "/stats"]
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
    Retrieve all tasks from SQLite.
    Supports status filtering (?done=true/false) and SQL LIKE searching (?search=query).
    """
    query = "SELECT id, title, done, created_at, updated_at FROM tasks"
    params = []
    conditions = []
    
    if done is not None:
        conditions.append("done = ?")
        params.append(1 if done else 0)
        
    if search is not None and search.strip():
        conditions.append("title LIKE ?")
        params.append(f"%{search.strip()}%")
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " ORDER BY title ASC"
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
        for row in rows
    ]

@app.get("/tasks/{id}")
def read_task(id: int):
    """
    Retrieve a single task by ID from SQLite using a parameterized query.
    Returns 404 if the task ID does not exist.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = ?", (id,))
        row = cursor.fetchone()
        
    if not row:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {id} not found"}
        )
        
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

@app.post("/tasks", status_code=201)
async def create_task(request: Request):
    """
    Create a new task in SQLite.
    Validates that title is a non-empty string (returns 400 Bad Request if missing/empty).
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
        
    if "title" not in body or not isinstance(body["title"], str) or not body["title"].strip():
        return JSONResponse(status_code=400, content={"error": "Title is required and cannot be empty"})
        
    title = body["title"].strip()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (title, done) VALUES (?, 0)", (title,))
        task_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute("SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

@app.put("/tasks/{id}")
async def update_task(id: int, request: Request):
    """
    Update a task's title and/or done status in SQLite using parameterized SQL.
    Returns 404 for unknown ID and 400 for invalid body.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (id,))
        existing = cursor.fetchone()
        
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
        new_done = 1 if body["done"] else 0
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tasks
            SET title = ?, done = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_title, new_done, id)
        )
        conn.commit()
        
        cursor.execute("SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = ?", (id,))
        row = cursor.fetchone()
        
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    """
    Remove a task from SQLite by ID.
    Returns 204 No Content on success, and 404 if the task ID does not exist.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tasks WHERE id = ?", (id,))
        existing = cursor.fetchone()
        
        if not existing:
            return JSONResponse(
                status_code=404,
                content={"error": f"Task {id} not found"}
            )
            
        cursor.execute("DELETE FROM tasks WHERE id = ?", (id,))
        conn.commit()
        
    return Response(status_code=204)

@app.get("/stats")
def get_stats():
    """
    Calculate task statistics directly in SQL using COUNT(*).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN done = 1 THEN 1 ELSE 0 END) AS done_count
            FROM tasks
        """)
        row = cursor.fetchone()
        
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
    Reset endpoint that clears the tasks table and re-seeds the 3 initial tasks inside a single transaction.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'tasks'")
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Learn FastAPI", 0),
                ("Set up Git", 1),
                ("Complete Stage 2", 0)
            ]
        )
        conn.commit()
        
    return {"status": "success", "message": "SQLite database reset to initial 3 seed tasks"}

