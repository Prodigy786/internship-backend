# Tiny Python Backend

A super lightweight, zero-dependency Python backend server exposing two JSON endpoints.

## How to Run

Run the server with Python:

```bash
python server.py
```

The server will start listening on `http://localhost:8000`.

## Endpoints

### 1. Welcome / Root Endpoint
* **URL:** `/`
* **Method:** `GET`
* **Response:** A message listing available endpoints.
* **Curl Command:**
  ```bash
  curl http://localhost:8000/
  ```

### 2. Hello Endpoint
* **URL:** `/api/hello`
* **Method:** `GET`
* **Response:** `{"message": "Hello, World!"}`
* **Curl Command:**
  ```bash
  curl http://localhost:8000/api/hello
  ```

### 3. Time Endpoint
* **URL:** `/api/time`
* **Method:** `GET`
* **Response:** Returns current UNIX epoch time and local human-readable time.
* **Curl Command:**
  ```bash
  curl http://localhost:8000/api/time
  ```
