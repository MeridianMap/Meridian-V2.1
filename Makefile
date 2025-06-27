.PHONY: install dev test lint build clean docker-build docker-run help

# Variables
BACKEND_DIR = backend
FRONTEND_DIR = frontend
PYTHON = python3
PIP = pip3
NPM = npm

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies (backend + frontend)
	@echo "Installing backend dependencies..."
	cd $(BACKEND_DIR) && $(PIP) install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && $(NPM) install

install-dev: ## Install development dependencies
	$(PIP) install flake8 black isort pytest pytest-cov
	cd $(FRONTEND_DIR) && $(NPM) install --include=dev

dev: ## Start development servers (backend + frontend)
	@echo "Starting development servers..."
	@echo "Backend will be available at http://localhost:5000"
	@echo "Frontend will be available at http://localhost:5173"
	$(PYTHON) -m $(BACKEND_DIR).api & cd $(FRONTEND_DIR) && $(NPM) run dev

dev-backend: ## Start only backend development server
	cd $(BACKEND_DIR) && $(PYTHON) api.py

dev-frontend: ## Start only frontend development server
	cd $(FRONTEND_DIR) && $(NPM) run dev

test: ## Run all tests
	@echo "Running backend tests..."
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest --cov=. --cov-report=term-missing
	@echo "Running frontend linting..."
	cd $(FRONTEND_DIR) && $(NPM) run lint

test-backend: ## Run backend tests only
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest --cov=. --cov-report=term-missing

lint: ## Run linting and formatting
	@echo "Linting backend..."
	cd $(BACKEND_DIR) && flake8 . --max-line-length=100
	cd $(BACKEND_DIR) && black --check .
	cd $(BACKEND_DIR) && isort --check-only .
	@echo "Linting frontend..."
	cd $(FRONTEND_DIR) && $(NPM) run lint

format: ## Format code (backend only)
	cd $(BACKEND_DIR) && black .
	cd $(BACKEND_DIR) && isort .

build: ## Build frontend for production
	cd $(FRONTEND_DIR) && $(NPM) run build

build-frontend: ## Build frontend only
	cd $(FRONTEND_DIR) && $(NPM) run build

docker-build: ## Build Docker image
	docker build -t meridian-v2.1 .

docker-run: ## Run Docker container locally
	docker run -p 5000:5000 -e PORT=5000 meridian-v2.1

clean: ## Clean build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf $(BACKEND_DIR)/.pytest_cache
	rm -rf $(FRONTEND_DIR)/dist
	rm -rf $(FRONTEND_DIR)/node_modules/.cache

render-deploy: ## Deploy to Render (requires render CLI)
	@echo "Deploying to Render..."
	@echo "Make sure you have connected your GitHub repo to Render"
	@echo "Push to main branch to trigger deployment"

env-setup: ## Copy example env files
	cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env
	cp $(FRONTEND_DIR)/.env.example $(FRONTEND_DIR)/.env
	@echo "Environment files created. Please edit them with your actual values."

health-check: ## Check if the API is running
	curl -f http://localhost:5000/api/health || echo "API not running on port 5000"
