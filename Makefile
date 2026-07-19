# Convenience targets. On Windows use Git Bash, or run the underlying commands directly.
.PHONY: help install backend frontend seed test lint fmt up

help:
	@echo "install   - install backend + frontend deps"
	@echo "backend   - run FastAPI dev server (:8000)"
	@echo "frontend  - run Vite dev server (:5173)"
	@echo "seed      - init db + load demo data"
	@echo "test      - run backend tests"
	@echo "up        - docker compose up"

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

seed:
	cd backend && python scripts/init_db.py && python scripts/seed_data.py

test:
	cd backend && pytest -q

lint:
	cd backend && ruff check app

fmt:
	cd backend && ruff format app

up:
	docker compose up --build
