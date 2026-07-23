# Task CRUD API (SQLite Edition — W3 Assignment 2)

A fast, persistent To-Do list CRUD API built with Python and FastAPI, backed by a real **SQLite** database (`tasks.db`). 

While client requests and API responses behave identically to Assignment 1, all data is now persisted to disk on a SQLite table, allowing task records to survive server restarts.

---

## 💡 Why SQLite?

1. **Zero Configuration & Serverless:** SQLite operates directly on a single local file (`tasks.db`) without requiring a separate database server daemon (like Postgres or MySQL) to install, configure, or maintain.
2. **File-Based Persistence:** Data lives on disk rather than volatile RAM, ensuring tasks outlive application restarts.
3. **Identical API Contracts:** Migrating from in-memory arrays to SQLite demonstrates that data storage is strictly an **implementation detail** — external clients continue sending the same requests to the same endpoints and receiving identical responses.

---

## 🚀 Installation & Running

1. **Activate virtual environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
2. **Install dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```
3. **Start the API server (1 command):**
   ```bash
   uvicorn main:app --reload
   ```
   The API will automatically create `tasks.db` and seed 3 default tasks if the database is missing.

---

## 📂 Database File Location & Schema

* **Database File:** `tasks.db` (located in the project root directory).
* **Git Policy:** `tasks.db` is included in `.gitignore` so every new clone starts clean with fresh database auto-creation and seeding.

### SQL Schema (`tasks` table)
```sql
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📖 API Endpoints & Status Codes

| Method | Endpoint | Request Body | Success | Error Codes | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | None | `200 OK` | None | API metadata and storage mode details. |
| **GET** | `/health` | None | `200 OK` | None | Server health status (`{"status": "ok"}`). |
| **GET** | `/tasks` | None | `200 OK` | None | Lists tasks from SQLite. Supports `done` status filter and SQL `search` term. |
| **GET** | `/tasks/{id}` | None | `200 OK` | `404 Not Found` | Fetches a single task from SQLite via parameterized query (`WHERE id = ?`). |
| **POST** | `/tasks` | `{ "title": "Text" }` | `201 Created` | `400 Bad Request` | Inserts a new task into SQLite. Returns auto-generated ID. |
| **PUT** | `/tasks/{id}` | `{ "title": "Text", "done": bool }` | `200 OK` | `400 Bad Request`, `404 Not Found` | Updates task title and/or completion status in SQLite. |
| **DELETE**| `/tasks/{id}` | None | `204 No Content`| `404 Not Found` | Deletes task row from SQLite by ID. |
| **GET** | `/stats` | None | `200 OK` | None | Computes `total`, `done`, and `open` counts via SQL `COUNT(*)`. |
| **POST** | `/reset` | None | `200 OK` | None | Clears table and re-seeds 3 default tasks in a single transaction. |

---

## 💻 Example Curl Output

Creating a new task and verifying disk persistence:

```http
HTTP/1.1 201 Created
date: Thu, 23 Jul 2026 05:47:06 GMT
server: uvicorn
content-length: 123
content-type: application/json

{"id":4,"title":"Buy organic groceries","done":false,"created_at":"2026-07-23 05:47:07","updated_at":"2026-07-23 05:47:07"}
```

---

## 🔍 Stage 4: SQL Exploration by Hand

Opening `tasks.db` directly using **DB Browser for SQLite** (or raw SQLite queries):

```sql
-- 1. List every task in the table
SELECT * FROM tasks;

-- 2. Fetch only completed tasks
SELECT * FROM tasks WHERE done = 1;

-- 3. Calculate total task count
SELECT COUNT(*) FROM tasks;

-- 4. Mark every task as completed
UPDATE tasks SET done = 1;

-- 5. Delete all completed tasks
DELETE FROM tasks WHERE done = 1;
```

**Observation:**
Executing queries by hand inside DB Browser directly modifies `tasks.db`. Immediately calling `GET /tasks` from curl or Swagger UI reflects these changes instantly without restarting the server — proving that the API and DB Browser share one single disk-backed source of truth.

---

## 🎯 Implementation Detail Proof

**Why identical API tests prove storage is just an implementation detail:**
Our Stage 4 curl test suite from Assignment 1 runs completely unchanged against this SQLite version and produces 100% identical HTTP status codes (`200`, `201`, `204`, `400`, `404`) and JSON payloads. 

The API defines the **contract** (what the application promises to do), while the database defines **where** the data is kept. Swapping the storage layer from memory to SQLite (or Postgres) keeps the exact same contract intact.

---

## 🤖 Stage 6: AI Rematch (AI vs Me)

This section compares our hand-built SQLite implementation in [main.py](file:///c:/Users/hp/Desktop/Internship%20assignment/main.py) against the AI-generated version in [ai-version/main.py](file:///c:/Users/hp/Desktop/Internship%20assignment/ai-version/main.py).

### The Prompt Used
```text
Migrate the Python FastAPI To-Do list CRUD API to use a SQLite database (ai_tasks.db).
1. Create a table named tasks with columns: id (INTEGER PRIMARY KEY AUTOINCREMENT), title (TEXT NOT NULL), and done (INTEGER NOT NULL DEFAULT 0).
2. On startup, create the table if missing, and seed 3 initial tasks ONLY if the table is empty.
3. Use parameterized SQL queries (?) for all CRUD operations.
4. Implement GET /, GET /health, GET /tasks, GET /tasks/{id}, POST /tasks (201 created, 400 bad request), PUT /tasks/{id} (200/400/404), and DELETE /tasks/{id} (204 no content, 404).
```

### Key Differences Observed
1. **Timestamp Auditing:**
   * **Hand-Built:** Included `created_at` and `updated_at` timestamps using SQLite `CURRENT_TIMESTAMP` for auditability and schema completeness.
   * **AI-Generated:** Created only basic `id`, `title`, and `done` columns without timestamp metadata.
2. **Schema Control & Isolation:**
   * **Hand-Built:** Stored data in the main application `tasks.db`.
   * **AI-Generated:** Isolated its database into `ai_tasks.db` within the `ai-version/` directory to prevent workspace collision.
3. **Transaction Management & Reset:**
   * **Hand-Built:** Included `POST /reset`, SQL status filtering, and SQL `COUNT(*)` aggregation endpoints (`/stats`).
   * **AI-Generated:** Stuck strictly to the core 5 CRUD endpoints and did not add statistics or table reset utilities.
