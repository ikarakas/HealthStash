.PHONY: help build up down logs restart clean backup restore test

help:
	@echo "HealthStash - Docker Management Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make build    - Build all Docker images"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make logs     - View logs for all services"
	@echo "  make restart  - Restart all services"
	@echo "  make clean    - Remove all containers and volumes"
	@echo "  make backup   - Create a backup"
	@echo "  make restore  - Restore from backup"
	@echo "  make test     - Run tests"
	@echo "  make init     - Initialize the application (first time setup)"

init:
	@chmod +x startup.sh
	@./startup.sh

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart

clean:
	docker-compose down -v
	rm -rf postgres_data timescale_data redis_data minio_data backup_data nginx_logs

backup:
	docker exec healthstash-backup /backup/backup.sh

restore:
	@echo "Please specify backup file path:"
	@read -p "Backup file: " backup_file; \
	docker exec healthstash-backup /backup/restore.sh $$backup_file

test:
	@echo "Running backend tests..."
	docker-compose exec backend pytest
	@echo "Running frontend tests..."
	docker-compose exec frontend npm test

# Development commands
dev-backend:
	docker-compose exec backend bash

dev-frontend:
	docker-compose exec frontend sh

dev-db:
	docker-compose exec postgres psql -U healthstash -d healthstash

# Service-specific logs
logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-postgres:
	docker-compose logs -f postgres

logs-nginx:
	docker-compose logs -f nginx

# Health checks
health:
	@echo "Checking service health..."
	@docker-compose ps
	@echo ""
	@echo "API Health:"
	@curl -s http://localhost:8000/health || echo "API is not responding"
	@echo ""
	@echo "Frontend Health:"
	@curl -s http://localhost/ || echo "Frontend is not responding"