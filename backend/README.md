## Backend API

A basic FastAPI backend application with health endpoints and test suite.

---

### 1. Setup & Installation

#### Create & Activate Virtual Environment

```bash
# From the project root
python3 -m venv backend/.venv
source backend/.venv/bin/activate
```

#### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

### 2. Running the Server

#### Option A: Direct with Uvicorn (Development)

From the project root:
```bash
backend/.venv/bin/uvicorn app.main:app --reload --app-dir backend --port 8000
```

Or from inside the `backend/` directory:
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

#### Option B: Run with Docker

```bash
cd backend
docker build -t backend-api .
docker run -p 8000:8000 backend-api
```

---

### 3. Endpoints & API Documentation

Once the server is running on `http://localhost:8000`:

| Endpoint | Method | Description | Example Response |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | Service status | `{"status":"ok","message":"API is running"}` |
| `/api/v1/health` | `GET` | Liveness health check | `{"status":"healthy"}` |
| `/api/v1/ready` | `GET` | Readiness check | `{"status":"ready"}` |
| `/docs` | `GET` | Swagger Interactive API UI | Interactive Docs |
| `/redoc` | `GET` | ReDoc API Documentation | ReDoc UI |

#### Quick Test with curl:

```bash
curl http://localhost:8000/api/v1/health
```
---

### 4. Running Tests

Run all unit tests using `pytest`:
```bash
cd backend
pytest tests/
```