# Makefile for Stock Market RAG App

.PHONY: help build up down restart logs clean

help: ## Show this help message
	@echo "Available commands:"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View logs"
	@echo "  make clean      - Remove all containers and images"

build: ## Build Docker images
	docker-compose build --no-cache

up: ## Start all services
	docker-compose up -d
	@echo "Services started!"
	@echo "Backend: http://localhost:8080"
	@echo "Frontend: http://localhost:8501"

down: ## Stop all services
	docker-compose down

restart: down up ## Restart all services

logs: ## View logs
	docker-compose logs -f

logs-backend: ## View backend logs only
	docker-compose logs -f backend

logs-frontend: ## View frontend logs only
	docker-compose logs -f frontend

clean: ## Remove all containers, images, and volumes
	docker-compose down -v --rmi all
	docker system prune -af
	@echo "Cleanup complete!"

status: ## Check service status
	docker-compose ps

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/bash
