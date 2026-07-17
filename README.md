# Task CRUD API

A premium, fast, and interactive in-memory To-Do Task CRUD API built with Python and FastAPI. It supports the full CRUD lifecycle, input validation, custom error responses, Swagger UI interactive documentation, and several extra features (filtering, title searching, stats tracking, and database reset).

## 🚀 Installation & Running

Follow these steps to run the API locally in under 5 minutes:

1. **Clone the repository** (or navigate to the workspace directory).
2. **Create a virtual environment** and activate it:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the server** with one command:
   ```bash
   .\venv\Scripts\uvicorn main:app --reload
   ```
   The API will start running at `http://127.0.0.1:8000`.

---

## 📂 API Endpoints

| Method | Endpoint | Request Body | Success Code | Error Codes | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | None | `200 OK` | None | Retrieves API name, version, and primary endpoints list. |
| **GET** | `/health` | None | `200 OK` | None | Health check endpoint returning `{ "status": "ok" }`. |
| **GET** | `/tasks` | None | `200 OK` | None | Lists all tasks. Supports optional query parameters: `done` (boolean) and `search` (case-insensitive string search). |
| **GET** | `/tasks/{id}` | None | `200 OK` | `404 Not Found` | Returns a single task by its ID. |
| **POST** | `/tasks` | `{ "title": "Text" }` | `201 Created` | `400 Bad Request` | Creates a new task. Checks that `title` is a non-empty string. |
| **PUT** | `/tasks/{id}` | `{ "title": "Text", "done": bool }` | `200 OK` | `400 Bad Request`, `404 Not Found` | Replaces/updates an existing task's title and/or done status. |
| **DELETE**| `/tasks/{id}` | None | `204 No Content`| `404 Not Found` | Deletes a task by ID. Returns empty body on success. |
| **GET** | `/stats` | None | `200 OK` | None | Returns counts for `total`, `done`, and `open` tasks. |
| **POST** | `/reset` | None | `200 OK` | None | Restores the default 3 seed tasks. |

---

## 💻 Example Curl Output

Here is the terminal output from creating a new task using `curl -i`:

```http
HTTP/1.1 201 Created
date: Fri, 17 Jul 2026 22:18:34 GMT
server: uvicorn
content-length: 43
content-type: application/json

{"id":4,"title":"Read a book","done":false}
```

---

## 🔍 Swagger UI Documentation

FastAPI automatically generates interactive Swagger UI documentation at:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

You can expand any endpoint, click **"Try it out"**, fill in the parameters, and click **"Execute"** to send live requests to the running server.

![Swagger UI Screenshot](swagger-screenshot.png)

---

## 🧪 The Mortality Experiment

**Observation:**
If we create new tasks (e.g. `id: 4` "Read a book"), restart the FastAPI server, and then execute `GET /tasks`, all the newly added tasks disappear and the database resets to the original 3 default seed tasks.

**Why this happens:**
Our API stores tasks in a standard Python list inside RAM (`in-memory`). Since RAM is volatile, all variables and data are wiped clean when the server process exits. To persist tasks across restarts, we need a non-volatile data storage solution, such as a database (SQL/NoSQL) or filesystem writes, which will be introduced in Week 3.

---

## 🤖 AI vs Me: Stage 7 Rematch

This section compares our hand-built implementation against the AI-generated quarantine version located in [ai-version/main.py](file:///c:/Users/hp/Desktop/Internship%20assignment/ai-version/main.py).

### The Prompt Used
```text
Write a Python FastAPI application for a To-Do list CRUD API.
It should store tasks in-memory in a list. The list should be pre-populated with 3 tasks (ids 1, 2, and 3) with properties: id (int), title (str), done (bool).

Implement the following endpoints:
1. GET / - returns JSON metadata: { "name": "Task API", "version": "1.0", "endpoints": ["/tasks"] }
2. GET /health - returns { "status": "ok" }
3. GET /tasks - returns the list of tasks.
4. GET /tasks/{id} - returns a single task. If task doesn't exist, return status 404 with JSON: { "error": "Task <id> not found" }
5. POST /tasks - creates a new task. Request body must contain a JSON object with 'title' (non-empty string). Sets done=False, assigns next free integer id, appends to the in-memory list, and returns the created task with status code 201. If title is missing or empty, returns 400 Bad Request with a JSON error.
6. PUT /tasks/{id} - replaces title and/or done status of a task based on the body. Returns the updated task. Returns 404 for unknown id, and 400 for empty/invalid body.
7. DELETE /tasks/{id} - removes the task from the list. Returns status code 204 with an empty body. Returns 404 for unknown id.

Ensure all endpoints are documented using docstrings so Swagger UI at /docs is informative.
```

### Key Differences Observed
1. **Pydantic vs. Manual Request Parsing:**
   * **Hand-Built:** We manually parsed raw JSON bodies from the FastAPI `Request` object asynchronously (`await request.json()`) and explicitly validated types and empty strings inside the route handlers. This kept the route logic self-contained but required async route handling.
   * **AI-Generated:** The AI used idiomatic FastAPI Pydantic models (`TaskCreate` and `TaskUpdate`) with field validators (`@field_validator`). This allowed all routing functions to be synchronous because Pydantic handles parsing automatically before execution.
2. **Handling 422 vs. 400 Error Codes:**
   * **Hand-Built:** Since we manually validated, returning a `400 Bad Request` was as simple as returning `JSONResponse(status_code=400, content={"error": "..."})`.
   * **AI-Generated:** By default, Pydantic validation failures return `422 Unprocessable Entity`. To conform to our spec requiring `400 Bad Request`, the AI registered a custom exception handler `@app.exception_handler(RequestValidationError)` that catches the validation errors, parses them into a custom detail string, and returns them as a `400` status JSON response.
3. **What was forgotten and silently decided:**
   * The prompt did not specify the exact format of the JSON validation error. The AI decided to format it as `{"error": "Bad Request: body -> title: Field required"}`.
   * The prompt did not specify how a `PUT` endpoint (which typically means full replacement) should handle partial updates. The AI resolved this by creating a `TaskUpdate` model with all optional fields and updating only the fields provided.
   * The hand-built version includes the optional extras (filtering, search, stats, reset) which make it a more complete and feature-rich server.

