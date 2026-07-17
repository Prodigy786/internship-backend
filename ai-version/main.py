from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(
    title="Task API",
    description="A Python FastAPI application for a To-Do list CRUD API.",
    version="1.0"
)

# In-memory database of tasks
tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Set up Git", "done": True},
    {"id": 3, "title": "Complete Stage 2", "done": False}
]

class TaskCreate(BaseModel):
    title: str = Field(..., description="The title of the task. Must be a non-empty string.")

    @field_validator('title')
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Title must be a non-empty string.")
        return value.strip()

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, description="The new title of the task. Must be a non-empty string if provided.")
    done: bool | None = Field(default=None, description="The completion status of the task.")

    @field_validator('title')
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is not None:
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Title must be a non-empty string.")
            return value.strip()
        return value

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom exception handler to return 400 Bad Request instead of 422 for validation errors.
    """
    errors = exc.errors()
    # Extract the error messages to be returned to the client
    error_details = []
    for error in errors:
        loc = " -> ".join(str(x) for x in error.get("loc", []))
        msg = error.get("msg", "Invalid value")
        error_details.append(f"{loc}: {msg}")
    
    error_msg = "; ".join(error_details)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": f"Bad Request: {error_msg}"}
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Custom exception handler for Starlette HTTPExceptions to ensure all error messages are returned in JSON format.
    """
    # Keep 404 for route not found formatted nicely, or other HTTPExceptions
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    """
    Retrieve metadata about the Task API, including name, version, and supported endpoints.
    """
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health", status_code=status.HTTP_200_OK)
def read_health():
    """
    Check the health status of the API application. Returns ok if active.
    """
    return {
        "status": "ok"
    }

@app.get("/tasks", status_code=status.HTTP_200_OK)
def read_tasks():
    """
    Retrieve the entire in-memory list of tasks.
    """
    return tasks

@app.get("/tasks/{id}", status_code=status.HTTP_200_OK)
def read_task(id: int):
    """
    Retrieve details of a single task by its unique ID.
    Returns 404 Not Found if the task ID does not exist in the database.
    """
    for task in tasks:
        if task["id"] == id:
            return task
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {id} not found"}
    )

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreate):
    """
    Create a new task and add it to the task list.
    Automatically assigns the next available unique integer ID and sets the completion status to False.
    """
    # Generate the next free integer ID
    next_id = max([t["id"] for t in tasks]) + 1 if tasks else 1
    new_task = {
        "id": next_id,
        "title": task_data.title,
        "done": False
    }
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{id}", status_code=status.HTTP_200_OK)
def update_task(id: int, task_data: TaskUpdate):
    """
    Update the title and/or done status of an existing task by its ID.
    Returns 404 Not Found if the ID does not exist, or 400 Bad Request if the request body is empty or invalid.
    """
    # Find the task
    task_idx = -1
    for i, task in enumerate(tasks):
        if task["id"] == id:
            task_idx = i
            break

    if task_idx == -1:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {id} not found"}
        )

    # Check if the update is empty (neither title nor done provided)
    # We can check task_data.model_fields_set or checking if title and done are both None.
    # Note: if they pass {"title": null, "done": null}, model_fields_set has them, but they are None.
    # So we check if both title and done are None.
    if task_data.title is None and task_data.done is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Request body must contain 'title' and/or 'done' status."}
        )

    # Apply updates
    if task_data.title is not None:
        tasks[task_idx]["title"] = task_data.title
    if task_data.done is not None:
        tasks[task_idx]["done"] = task_data.done

    return tasks[task_idx]

@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int):
    """
    Remove a task from the list by its ID.
    Returns status code 204 No Content upon successful deletion, or 404 Not Found if the ID does not exist.
    """
    for i, task in enumerate(tasks):
        if task["id"] == id:
            tasks.pop(i)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {id} not found"}
    )
