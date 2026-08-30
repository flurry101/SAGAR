.PHONY: up down build test test-local check-conn check-conn-prod logs restart ps

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose up --build -d backend

test:
	docker compose exec backend pytest tests/ -v

test-local:
	backend/.venv/bin/pytest backend/tests/ -v

check-conn:
	backend/.venv/bin/python backend/scripts/test_supabase_connection.py

check-conn-prod:
	ENV_FILE=.env.production backend/.venv/bin/python backend/scripts/test_supabase_connection.py

logs:
	docker compose logs -f backend

restart:
	docker compose restart backend

ps:
	docker compose ps
