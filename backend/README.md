## Backend

FastAPI backend with supabase jwt auth, postgres persistence, health monitoring, tests.

---

### 1. Setup & Installation

#### Create & Activate Virtual Environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### 2. Environment Configuration

Copy the example environment configuration:
```bash
cp .env.example .env
```

Key environment variables:
- `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Local PostgreSQL settings.
- `DATABASE_URL`: (Optional) Direct connection URI; defaults to local PostgreSQL or set to Supabase transaction pooler in production.
- `SUPABASE_PROJECT_ID`: Supabase project reference id.
- `SUPABASE_JWT_SECRET`: JWT Secret from `Project Settings > API > JWT Settings`.

---

### 3. Running the Server

#### Option A: Local Development with Uvicorn

1. Ensure local PostgreSQL is running:
   ```bash
   docker run -d --name sagar_postgres -p 5432:5432 \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=postgrespassword \
     -e POSTGRES_DB=sagar_db \
     postgres:16-alpine
   ```

2. Start the FastAPI server:
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn app.main:app --reload --port 8000
   ```

#### Option B: Docker Compose (Root Directory)

```bash
docker compose up --build -d
```

#### Option C: Production Docker Container (Connected to Supabase)

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

---

### 4. Endpoints & API Documentation

Once the server is running on `http://localhost:8000`:

| Endpoint | Method | Auth | Description |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | None | Service status |
| `/api/v1/health` | `GET` | None | Liveness health check |
| `/api/v1/ready` | `GET` | None | Readiness check |
| `/api/v1/user/create` | `POST` | Supabase JWT | Sync/create user profile in database |
| `/api/v1/user/me` | `GET` | Supabase JWT | Get authenticated user profile |
| `/api/v1/user/me` | `PUT` | Supabase JWT | Update user profile |
| `/api/v1/user/token-info` | `GET` | Supabase JWT | Inspect parsed token claims |
| `/user/create` | `POST` | Supabase JWT | Starter compatibility user create |
| `/user/me` | `GET` | Supabase JWT | Starter compatibility user me |
| `/docs` | `GET` | None | Swagger Interactive API UI |
| `/redoc` | `GET` | None | ReDoc API Documentation |

---

### 5. Running Tests

Run all unit tests using `pytest`:
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```
