# FabriSee developer commands. Run `make help` for the list.

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Python 3.12 if it is installed under that name, otherwise the default python3.
PYTHON ?= $(shell command -v python3.12 2>/dev/null || command -v python3)
VENV := backend/.venv
BIN := $(VENV)/bin
MANAGE := cd backend && .venv/bin/python manage.py

.PHONY: help setup env backend-install frontend-install migrate seed reset-demo dev \
        test test-backend test-frontend lint format e2e screenshots build lock clean

help: ## Show this list
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: env backend-install frontend-install migrate seed ## Install dependencies, migrate, and load the demo data
	@echo ""
	@echo "Setup complete. Run 'make dev' and open http://localhost:5173"

env: ## Create .env from .env.example (an existing .env is kept)
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		$(PYTHON) -c "import pathlib, secrets; p = pathlib.Path('.env'); p.write_text(p.read_text().replace('change-me-generated-by-make-setup', secrets.token_urlsafe(50)))"; \
		echo "Created .env with a new SECRET_KEY"; \
	fi

backend-install: ## Create the virtual environment and install Python packages
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@$(BIN)/python -m pip install --quiet --upgrade pip
	$(BIN)/python -m pip install --quiet -r backend/requirements-dev.txt

frontend-install: ## Install Node packages from the lock file
	cd frontend && npm ci --no-audit --no-fund

migrate: ## Apply database migrations
	$(MANAGE) migrate --noinput

seed: ## Load the demo data (does nothing if it is already loaded)
	$(MANAGE) seed_demo

reset-demo: ## Delete all data and uploads, then load fresh demo data
	$(MANAGE) reset_demo --yes

dev: ## Run Django (port 8000), Vite (port 5173), and the scheduler together
	@if [ ! -x $(BIN)/honcho ] || [ ! -d frontend/node_modules ]; then \
		echo "Dependencies are missing. Run 'make setup' first."; exit 1; \
	fi
	@if $(BIN)/python -c "import socket, sys; s = socket.socket(); s.settimeout(0.5); sys.exit(0 if s.connect_ex(('127.0.0.1', 5173)) == 0 else 1)"; then \
		echo "FabriSee is already running. Open http://localhost:5173 (or the forwarded port 5173 in Codespaces)."; \
	else \
		$(BIN)/honcho start -f Procfile.dev; \
	fi

test: test-backend test-frontend ## ruff, pytest, ESLint, Prettier, TypeScript check, Vitest

test-backend: ## ruff, missing-migration check, pytest
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .
	$(MANAGE) makemigrations --check --dry-run
	cd backend && .venv/bin/python -m pytest

test-frontend: ## ESLint, Prettier, TypeScript check, Vitest
	cd frontend && npm run lint && npm run typecheck && npm test

lint: ## Linters only (ruff, ESLint, Prettier)
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .
	cd frontend && npm run lint

format: ## Format the code (ruff, Prettier)
	cd backend && .venv/bin/ruff check --fix . && .venv/bin/ruff format .
	cd frontend && npm run format

e2e: ## Playwright end-to-end tests (browsers: `npx playwright install chromium` in frontend/)
	cd frontend && npx playwright test --project=e2e

screenshots: ## Capture the key screens into docs/screenshots (desktop and phone sizes)
	cd frontend && npx playwright test --project=screenshots

build: ## Production build of the React app (frontend/dist)
	cd frontend && npm run build

lock: ## Regenerate the pinned Python requirements from the .in files (needs uv)
	cd backend && uv pip compile requirements.in --universal --python-version 3.12 \
		--custom-compile-command "make lock" -q -o requirements.txt
	cd backend && uv pip compile requirements-dev.in --universal --python-version 3.12 \
		--custom-compile-command "make lock" -q -o requirements-dev.txt

clean: ## Remove build output and caches (keeps the database and uploads)
	rm -rf frontend/dist frontend/coverage frontend/test-results frontend/playwright-report
	find backend -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/htmlcov backend/.coverage
