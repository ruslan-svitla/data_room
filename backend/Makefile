# Backend Makefile
# Uses UV for dependency management and virtual environment creation

# Configuration
APP_NAME = backend
PYTHON_VERSION = 3.12
VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
UV = uv
PIP = $(VENV_DIR)/bin/pip
DOCKER_IMAGE = $(APP_NAME)
DOCKER_CONTAINER = $(APP_NAME)-container
DOCKER_PORT = 8000

# Colors for terminal output
BOLD = \033[1m
GREEN = \033[32m
YELLOW = \033[33m
RESET = \033[0m

.PHONY: help setup install install-dev run dev test lint format clean docker-build docker-run docker-stop init-db migrate migrate-up migrate-down uvloop run-with-init init-dev-env activate-venv

help:
	@echo "$(BOLD)Available commands:$(RESET)"
	@echo "$(GREEN)setup$(RESET) - Create virtual environment using UV with Python $(PYTHON_VERSION) and install dependencies"
	@echo "$(GREEN)install$(RESET) - Install dependencies using UV"
	@echo "$(GREEN)install-dev$(RESET) - Install development dependencies using UV"
	@echo "$(GREEN)activate-venv$(RESET) - Activate the virtual environment (for shell scripts)"
	@echo "$(GREEN)init-dev-env$(RESET) - Complete development environment setup (setup, install-dev, database initialization)"
	@echo "$(GREEN)run$(RESET) - Run the application using UV"
	@echo "$(GREEN)dev$(RESET) - Run the application in development mode with auto-reload"
	@echo "$(GREEN)test$(RESET) - Run tests"
	@echo "$(GREEN)lint$(RESET) - Run linters (ruff, mypy)"
	@echo "$(GREEN)format$(RESET) - Format code using ruff"
	@echo "$(GREEN)clean$(RESET) - Clean cache files"
	@echo "$(GREEN)init-db$(RESET) - Initialize database with sample data"
	@echo "$(GREEN)migrate m=\"message\"$(RESET) - Generate new migration"
	@echo "$(GREEN)migrate-up$(RESET) - Apply migrations"
	@echo "$(GREEN)migrate-down$(RESET) - Rollback last migration"
	@echo "$(GREEN)uvloop$(RESET) - Install uvloop for improved performance"
	@echo "$(GREEN)run-with-init$(RESET) - Initialize database and run app in development mode"

uvloop:
	@echo "$(YELLOW)Installing uvloop for improved performance...$(RESET)"
	$(PIP) install uvloop

setup:
	@echo "$(YELLOW)Setting up virtual environment with Python $(PYTHON_VERSION) using UV...$(RESET)"
	uv venv -p $(PYTHON_VERSION) $(VENV_DIR)
	@echo "$(GREEN)Virtual environment created and dependencies installed.$(RESET)"

install:
	@test -d $(VENV_DIR) || (echo "$(YELLOW)Virtual environment not found. Run 'make setup' first.$(RESET)" && exit 1)
	@echo "$(YELLOW)Installing dependencies using UV...$(RESET)"
	$(UV) sync
	@echo "$(GREEN)Dependencies installed.$(RESET)"

install-dev:
	@test -d $(VENV_DIR) || (echo "$(YELLOW)Virtual environment not found. Run 'make setup' first.$(RESET)" && exit 1)
	@echo "$(YELLOW)Installing development dependencies using UV...$(RESET)"
	$(UV) pip install -e ".[dev]"
	@echo "$(GREEN)Development dependencies installed.$(RESET)"

run:
	@echo "$(YELLOW)Running application...$(RESET)"
	$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

dev:
	@echo "$(YELLOW)Running application in development mode...$(RESET)"
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "$(YELLOW)Running tests...$(RESET)"
	$(PYTHON) -m pytest -v --cov=app tests/


test-report:
	@echo "$(YELLOW)Running tests with coverage HTML report...$(RESET)"
	$(PYTHON) -m pytest -v --cov=app --cov-report=html tests/

lint:
	@echo "$(YELLOW)Running linters...$(RESET)"
	$(PYTHON) -m ruff check .

format:
	@echo "$(YELLOW)Formatting code...$(RESET)"
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .

clean:
	@echo "$(YELLOW)Cleaning cache files...$(RESET)"
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +

init-db:
	@echo "$(YELLOW)Initializing database...$(RESET)"
	$(PYTHON) -m app.db.init_db

init-db-data:
	@echo "$(YELLOW)Initializing database with data only...$(RESET)"
	$(PYTHON) initial_data.py

migrate:
	@echo "$(YELLOW)Generating migration: $(m)...$(RESET)"
	alembic revision --autogenerate -m "$(m)"

migrate-up:
	@echo "$(YELLOW)Applying migrations...$(RESET)"
	alembic upgrade head

migrate-down:
	@echo "$(YELLOW)Rolling back last migration...$(RESET)"
	alembic downgrade -1

activate-venv:
	@echo "$(YELLOW)Activating virtual environment...$(RESET)"
	@test -d $(VENV_DIR) || (echo "$(YELLOW)Virtual environment not found. Run 'make setup' first.$(RESET)" && exit 1)
	@echo 'Run: source $(VENV_DIR)/bin/activate'

init-dev-env:
	@echo "$(YELLOW)Setting up complete development environment...$(RESET)"
	$(MAKE) setup
	$(MAKE) activate-venv
	$(MAKE) install-dev
	$(MAKE) migrate-up
	$(MAKE) init-db
	$(MAKE) init-db-data
	@echo "$(GREEN)Development environment fully initialized!$(RESET)"
	@echo "$(YELLOW)To start working, activate the virtual environment with: $(BOLD)source $(VENV_DIR)/bin/activate$(RESET)"
