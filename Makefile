.PHONY: help setup dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend format build clean check-compliance check-secrets

help:
	@echo "Available Makefile targets:"
	@echo "  setup             Install all dependencies for backend and frontend"
	@echo "  dev               Run backend and frontend development servers concurrently"
	@echo "  dev-backend       Run FastAPI backend with reload"
	@echo "  dev-frontend      Run Vite development server"
	@echo "  test              Run all backend and frontend tests"
	@echo "  test-backend      Run pytest suite"
	@echo "  test-frontend     Run vitest and playwright tests"
	@echo "  lint              Run ruff and eslint"
	@echo "  lint-backend      Run ruff check and format check"
	@echo "  lint-frontend     Run eslint and typecheck"
	@echo "  format            Format code with ruff and prettier"
	@echo "  build             Build backend package and frontend production bundle"
	@echo "  clean             Remove cache, build artifacts, and virtual environments"
	@echo "  check-compliance  Verify zero emojis and zero unicode dashes"
	@echo "  check-secrets     Scan for committed credentials"

setup:
	uv venv --python 3.12
	uv pip install -e ".[dev]"
	cd frontend && npm install

dev:
	@echo "Starting backend and frontend services..."
	make -j 2 dev-backend dev-frontend

dev-backend:
	uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	uv run pytest tests/ -v

test-frontend:
	cd frontend && npm run test

lint: lint-backend lint-frontend check-compliance check-secrets

lint-backend:
	uv run ruff check backend/ tests/
	uv run ruff format --check backend/ tests/

lint-frontend:
	cd frontend && npm run lint && npm run typecheck

format:
	uv run ruff format backend/ tests/
	uv run ruff check --fix backend/ tests/
	cd frontend && npm run format

build:
	uv run python -m build backend/ || true
	cd frontend && npm run build

clean:
	rm -rf .venv __pycache__ .pytest_cache .ruff_cache frontend/dist frontend/node_modules
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

check-compliance:
	python3 scripts/check_compliance.py

check-secrets:
	python3 scripts/scan_secrets.py
