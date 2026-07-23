# Task CRUD API (PostgreSQL + Docker Edition — A3 Assignment)

A fast, persistent To-Do list CRUD API built with Python and FastAPI, now backed by a **PostgreSQL** database running inside Docker. The entire stack (API + database) is orchestrated with a single `docker compose up` command.

---

## 💡 Why PostgreSQL over SQLite?

1. **Server-Based Architecture:** PostgreSQL runs as a dedicated service in its own container, making it suitable for multi-container and production-grade deployments.
2. **Native Boolean Type:** PostgreSQL has a native `BOOLEAN` type (instead of SQLite's `INTEGER 0/1` workaround), keeping data semantically correct.
3. **`RETURNING` Clause:** `INSERT` and `UPDATE` statements use `RETURNING` to fetch the newly created/updated row in a single SQL round-trip, eliminating an extra `SELECT`.
4. **`TRUNCATE … RESTART IDENTITY`:** Clean table reset that resets the auto-increment sequence, ensuring IDs always restart from 1.
5. **`ILIKE` Search:** Case-insensitive `ILIKE` search (vs SQLite's `LIKE`) for more intuitive text filtering.
6. **Identical API Contracts:** Migrating from SQLite to PostgreSQL is purely an implementation detail — clients send the same requests and receive identical responses.

---

## 🚀 Quick Start (One Command)

> **Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) must be installed and running.

```bash
docker compose up
```

This single command will:
1. Pull `postgres:15-alpine` and build the FastAPI image.
2. Start the `db` service (PostgreSQL) and wait until it's healthy.
3. Start the `api` service on **port 3000**, auto-creating the `tasks` table and seeding 3 default tasks.

API available at: **http://localhost:3000**
Interactive docs: **http://localhost:3000/docs**

---

## 🔧 Local Development (Without Docker)

1. **Configure credentials:**
   ```bash
   cp .env.example .env
   # Edit .env and set DATABASE_URL to point to your local Postgres instance
   ```
2. **Activate virtual environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Start the API:**
   ```bash
   uvicorn main:app --reload --port 3000
   ```

---

## 🔐 Secrets Management

| File | Purpose | Git Status |
|:---|:---|:---|
| `.env` | Local credentials (real values) | ❌ git-ignored |
| `.env.example` | Template with placeholder values | ✅ committed |

The `DATABASE_URL` environment variable follows the format:
```
postgres://USER:PASSWORD@HOST:PORT/DATABASE
```

In Docker Compose, `DATABASE_URL` is injected directly via the `environment:` block in `compose.yaml`, so no `.env` file is needed inside the container.

---

## 🐳 Docker Architecture

```
┌─────────────────────────────────────────────┐
│              Docker Compose                  │
│                                             │
│  ┌──────────────┐    ┌──────────────────┐   │
│  │   api         │───▶│      db          │   │
│  │ (FastAPI)     │    │ (postgres:15-    │   │
│  │ port 3000     │    │  alpine)         │   │
│  └──────────────┘    └──────────┬───────┘   │
│                                 │            │
│                         Volume: taskdata     │
└─────────────────────────────────────────────┘
```

- **`api`**: Built from `Dockerfile` using `python:3.11-slim`.
- **`db`**: Official `postgres:15-alpine` image; data persisted in named volume `taskdata`.
- **Healthcheck**: `api` waits until `db` passes `pg_isready` before starting.

---

## 📂 Database Schema

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id         SERIAL PRIMARY KEY,
    title      TEXT NOT NULL,
    done       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key differences vs SQLite version:**
- `SERIAL` (auto-increment) instead of `INTEGER PRIMARY KEY AUTOINCREMENT`
- `BOOLEAN` instead of `INTEGER (0/1)`

---

## 📖 API Endpoints & Status Codes

| Method | Endpoint | Request Body | Success | Error Codes | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | None | `200 OK` | None | API metadata and storage mode details. |
| **GET** | `/health` | None | `200 OK` | None | Server health status (`{"status": "ok"}`). |
| **GET** | `/tasks` | None | `200 OK` | None | Lists tasks from PostgreSQL. Supports `done` filter and `ILIKE` `search`. |
| **GET** | `/tasks/{id}` | None | `200 OK` | `404 Not Found` | Fetches a single task via `WHERE id = %s`. |
| **POST** | `/tasks` | `{ "title": "Text" }` | `201 Created` | `400 Bad Request` | Inserts a new task using `RETURNING`. |
| **PUT** | `/tasks/{id}` | `{ "title": "Text", "done": bool }` | `200 OK` | `400`, `404` | Updates task using `UPDATE … RETURNING`. |
| **DELETE**| `/tasks/{id}` | None | `204 No Content`| `404 Not Found` | Deletes task row using `DELETE … RETURNING`. |
| **GET** | `/stats` | None | `200 OK` | None | Computes `total`, `done`, and `open` counts via `COUNT(*)`. |
| **POST** | `/reset` | None | `200 OK` | None | Clears table with `TRUNCATE RESTART IDENTITY` and re-seeds 3 tasks. |

---

## 💻 Example Curl Output

```bash
# Create a new task
curl -s -X POST http://localhost:3000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy organic groceries"}' | python -m json.tool
```

```json
{
    "id": 4,
    "title": "Buy organic groceries",
    "done": false,
    "created_at": "2026-07-23T07:47:06.123456",
    "updated_at": "2026-07-23T07:47:06.123456"
}
```

```bash
# Get stats
curl -s http://localhost:3000/stats | python -m json.tool
```

```json
{
    "total": 4,
    "done": 1,
    "open": 3
}
```

---

## 🔍 Stage 4: PostgreSQL Exploration by Hand

Connect to the running database container:

```bash
docker exec -it <container_name> psql -U postgres -d tasks
```

```sql
-- 1. List every task
SELECT * FROM tasks;

-- 2. Fetch only completed tasks
SELECT * FROM tasks WHERE done IS TRUE;

-- 3. Calculate total task count
SELECT COUNT(*) FROM tasks;

-- 4. Mark every task as completed
UPDATE tasks SET done = TRUE;

-- 5. Delete all completed tasks
DELETE FROM tasks WHERE done IS TRUE;

-- 6. Clean reset with identity restart
TRUNCATE TABLE tasks RESTART IDENTITY;
```

**Observation:** Running `UPDATE tasks SET done = TRUE` inside psql and then calling `GET /tasks` from curl immediately reflects the change — proving the API and psql share one single Postgres source of truth.

---

## 🎯 Implementation Detail Proof

The full CRUD test suite from A1/A2 runs completely unchanged against this PostgreSQL+Docker version, producing 100% identical HTTP status codes (`200`, `201`, `204`, `400`, `404`) and JSON payloads. The storage engine is strictly an implementation detail — swapping SQLite for PostgreSQL leaves the contract intact.

---

## 🤖 Stage 6: AI Rematch (AI vs Me)

This section compares our hand-built PostgreSQL implementation in [main.py](file:///c:/Users/hp/Desktop/Internship%20assignment/main.py) against the AI-generated version in [ai-version/main.py](file:///c:/Users/hp/Desktop/Internship%20assignment/ai-version/main.py).

### The Prompt Used
```text
Migrate the Python FastAPI To-Do list CRUD API to use a PostgreSQL database via psycopg.
1. Read DATABASE_URL from an environment variable (use python-dotenv for local dev).
2. Create a table named tasks with columns: id (SERIAL PRIMARY KEY), title (TEXT NOT NULL), done (BOOLEAN NOT NULL DEFAULT FALSE).
3. On startup, create the table if missing, and seed 3 initial tasks ONLY if the table is empty.
4. Use parameterized SQL queries (%s) for all CRUD operations.
5. Implement GET /, GET /health, GET /tasks, GET /tasks/{id}, POST /tasks (201/400), PUT /tasks/{id} (200/400/404), DELETE /tasks/{id} (204/404).
```

### Key Differences Observed

| Feature | Hand-Built | AI-Generated |
|:---|:---|:---|
| **Timestamp Auditing** | ✅ `created_at` + `updated_at` columns | ❌ No timestamps |
| **`ILIKE` Search** | ✅ Case-insensitive title search | ❌ Not implemented |
| **Status Filtering** | ✅ `?done=true/false` filter | ❌ Not implemented |
| **`/stats` Endpoint** | ✅ SQL `COUNT(*)` aggregation | ❌ Not implemented |
| **`/reset` Endpoint** | ✅ `TRUNCATE RESTART IDENTITY` | ❌ Not implemented |
| **`RETURNING` on UPDATE** | ✅ Single round-trip UPDATE | ✅ Same approach |
| **Healthcheck in Compose** | ✅ `pg_isready` healthcheck | ❌ Not in compose |
