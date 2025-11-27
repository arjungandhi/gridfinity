.PHONY: help venv install test lint format clean run view

# Variables
VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Default target - show help
help:
	@echo "Gridfinity Project - Available Commands:"
	@echo ""
	@echo "  make install    - Create venv and install dependencies"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run ruff linter"
	@echo "  make format     - Format code with ruff"
	@echo "  make fix        - Run ruff with auto-fix"
	@echo "  make run        - Run the main application"
	@echo "  make view       - Watch and display output.stl with f3d"
	@echo "  make clean      - Remove venv and cache files"
	@echo "  make clean-all  - Remove venv, cache, and build artifacts"

# Create virtual environment
$(VENV)/bin/activate:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	@echo "Virtual environment created!"

# Install dependencies
install: $(VENV)/bin/activate
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt
	@echo "Dependencies installed!"

# Install development dependencies
install-dev: install
	@if [ -f requirements-dev.txt ]; then \
		$(PIP) install -r requirements-dev.txt; \
	fi

# Run tests
test: install
	@echo "Running tests..."
	@if [ -d tests ]; then \
		$(PYTHON) -m pytest tests/ -v; \
	else \
		echo "No tests directory found. Create tests/ to add tests."; \
	fi

# Lint code with ruff
lint: install
	@echo "Running ruff linter..."\PlugInstall
	@if $(PIP) list | grep -q ruff; then \
		$(PYTHON) -m ruff check .; \
	else \
		echo "ruff not installed. Run: make install-dev"; \
	fi

# Format code with ruff
format: install
	@echo "Formatting code with ruff..."
	@if $(PIP) list | grep -q ruff; then \
		$(PYTHON) -m ruff format .; \
	else \
		echo "ruff not installed. Run: make install-dev"; \
	fi

# Lint and auto-fix with ruff
fix: install
	@echo "Running ruff with auto-fix..."
	@if $(PIP) list | grep -q ruff; then \
		$(PYTHON) -m ruff check --fix .; \
	else \
		echo "ruff not installed. Run: make install-dev"; \
	fi

# Run main application (customize this for your project)
run: install
	@if [ -f main.py ]; then \
		$(PYTHON) main.py; \
	else \
		echo "No main.py found. Create one or update this target."; \
	fi

# Watch and display 3D model with f3d
view:
	@mkdir -p outputs
	@if ! command -v f3d &> /dev/null; then \
		echo "f3d not found. Install it with:"; \
		echo "  sudo apt install f3d"; \
		echo "  or visit https://f3d.app/"; \
		exit 1; \
	fi
	@if [ ! -f outputs/output.stl ]; then \
		echo "outputs/output.stl not found. Run 'make run' first."; \
		exit 1; \
	fi
	@echo "Watching outputs/output.stl with f3d..."
	@echo "The viewer will auto-reload when the file changes."
	f3d --watch outputs/output.stl

# Clean cache files
clean:
	@echo "Cleaning cache files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf .coverage htmlcov/
	@echo "Cache files cleaned!"

# Clean everything including venv
clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	@echo "Everything cleaned!"

# Freeze current dependencies
freeze: install
	$(PIP) freeze > requirements.txt
	@echo "Dependencies frozen to requirements.txt"
