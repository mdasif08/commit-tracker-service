#!/bin/bash

# Commit Tracker Service Startup Script

set -e

echo "Starting Commit Tracker Service..."

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

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp env.example .env
    echo "Please update .env file with your configuration"
fi

# Check database connection
echo "Checking database connection..."
python3 -c "
import asyncio
import sys
sys.path.append('src')
from database import get_db_service, close_db_service

async def check_db():
    try:
        db_service = await get_db_service()
        if await db_service.health_check():
            print('Database connection: OK')
        else:
            print('Database connection: FAILED')
            sys.exit(1)
    except Exception as e:
        print(f'Database connection error: {e}')
        sys.exit(1)
    finally:
        await close_db_service()

asyncio.run(check_db())
"

# Start the service
echo "Starting Commit Tracker Service on http://localhost:8001"
echo "Press Ctrl+C to stop"

uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
