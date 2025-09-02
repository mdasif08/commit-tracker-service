.PHONY: help install test lint format clean docker-build docker-run docker-stop

help: ## Show this help message
	@echo "Commit Tracker Service - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

test: ## Run tests
	pytest tests/ -v

test-api: ## Test API endpoints
	python test.py

test-coverage: ## Run tests with coverage
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint: ## Run linting
	black --check src/ tests/
	isort --check-only src/ tests/
	flake8 src/ tests/

format: ## Format code
	black src/ tests/
	isort src/ tests/

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/

docker-build: ## Build Docker image
	docker build -t commit-tracker-service:latest .

docker-run: ## Run with Docker Compose
	docker-compose up -d

docker-stop: ## Stop Docker Compose services
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f commit-tracker-service

start: ## Start the service locally
	python start.py

dev: ## Start in development mode
	DEBUG=true LOG_LEVEL=debug python start.py

health: ## Check service health
	curl -f http://localhost:8001/health || echo "Service is not running"

metrics: ## Get service metrics
	curl http://localhost:8001/metrics
