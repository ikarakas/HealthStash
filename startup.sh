#!/bin/bash

set -e

echo "Starting HealthStash..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    
    # Generate secure keys
    echo "Generating secure keys..."
    SECRET_KEY=$(openssl rand -base64 32)
    ENCRYPTION_KEY=$(openssl rand -base64 32)
    JWT_SECRET_KEY=$(openssl rand -base64 32)
    
    # Update .env file with generated keys
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        sed -i '' "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
        sed -i '' "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET_KEY/" .env
    else
        # Linux
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
        sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET_KEY/" .env
    fi
    
    echo "Generated secure keys in .env file"
    echo "IMPORTANT: Please update the database passwords in .env before continuing!"
    echo "Press Enter to continue after updating passwords..."
    read
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p nginx/ssl
mkdir -p backups

# Build and start containers
echo "Building Docker images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check health
echo "Checking service health..."
docker-compose ps

echo ""
echo "HealthStash is starting up!"
echo ""
echo "Access the application at:"
echo "  Web Interface: http://localhost"
echo "  API Documentation: http://localhost:8000/docs"
echo ""
echo "Default admin account:"
echo "  The first user to register becomes the admin"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f [service_name]"
echo ""
echo "To stop the application:"
echo "  docker-compose down"
echo ""