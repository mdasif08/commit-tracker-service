#!/bin/bash

# Commit Tracker Service Test Script

set -e

echo "Running Commit Tracker Service tests..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run linting
echo "Running code linting..."
echo "Running black..."
black --check src/ tests/
echo "Running isort..."
isort --check-only src/ tests/
echo "Running flake8..."
flake8 src/ tests/

# Run tests
echo "Running tests..."
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

echo "Tests completed successfully!"
