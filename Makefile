.PHONY: up down build build-backend build-frontend test test-local check-conn check-conn-prod logs logs-backend logs-frontend restart restart-backend restart-frontend ps

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose up --build -d

build-backend:
	docker compose up --build -d backend

build-frontend:
	docker compose up --build -d frontend

test:
	docker compose exec backend pytest tests/ -v

test-local:
	backend/.venv/bin/pytest backend/tests/ -v

check-conn:
	backend/.venv/bin/python backend/scripts/test_supabase_connection.py

check-conn-prod:
	ENV_FILE=.env.production backend/.venv/bin/python backend/scripts/test_supabase_connection.py

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

restart:
	docker compose restart

restart-backend:
	docker compose restart backend

restart-frontend:
	docker compose restart frontend

ps:
	docker compose ps
