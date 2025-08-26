#!/bin/bash

# Deployment script for Commit Tracker Service

set -e

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}

echo "Deploying Commit Tracker Service to $ENVIRONMENT (version: $VERSION)"

# Load environment-specific configuration
if [ -f "config/$ENVIRONMENT.env" ]; then
    source "config/$ENVIRONMENT.env"
    echo "Loaded configuration for $ENVIRONMENT"
else
    echo "Warning: No environment configuration found for $ENVIRONMENT"
fi

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    echo "Error: Environment must be 'staging' or 'production'"
    exit 1
fi

# Deploy using Docker Compose
echo "Starting deployment with Docker Compose..."
if [ -f "docker-compose.$ENVIRONMENT.yml" ]; then
    docker-compose -f docker-compose.yml -f docker-compose.$ENVIRONMENT.yml up -d
else
    docker-compose up -d
fi

# Wait for service to be healthy
echo "Waiting for service to be healthy..."
timeout=60
while [ $timeout -gt 0 ]; do
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Service is healthy!"
        break
    fi
    echo "Waiting for service to be ready... ($timeout seconds remaining)"
    sleep 5
    timeout=$((timeout - 5))
done

if [ $timeout -le 0 ]; then
    echo "❌ Service failed to become healthy"
    echo "Checking service logs..."
    docker-compose logs commit-tracker-service
    exit 1
fi

# Run smoke tests
echo "Running smoke tests..."
if curl -f http://localhost:8001/health | grep -q "healthy"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

if curl -f http://localhost:8001/metrics > /dev/null 2>&1; then
    echo "✅ Metrics endpoint accessible"
else
    echo "❌ Metrics endpoint failed"
    exit 1
fi

echo "🎉 Deployment completed successfully!"
echo "Service is running at: http://localhost:8001"
echo "Health check: http://localhost:8001/health"
echo "API docs: http://localhost:8001/api/docs"
