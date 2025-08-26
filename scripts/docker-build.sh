#!/bin/bash

# Commit Tracker Service Docker Build Script

set -e

echo "Building Commit Tracker Service Docker image..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# Build the Docker image
echo "Building Docker image..."
docker build -t commit-tracker-service:latest .

echo "Docker image built successfully!"
echo "To run the service with Docker Compose:"
echo "  docker-compose up -d"
echo ""
echo "To run the service directly:"
echo "  docker run -p 8001:8001 commit-tracker-service:latest"
