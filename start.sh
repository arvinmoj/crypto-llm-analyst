#!/bin/bash

# Start script for crypto-llm-analyst
# This script starts the FastAPI application with proper configuration

set -e

# Default values
HOST=${API_HOST:-"0.0.0.0"}
PORT=${API_PORT:-8000}
WORKERS=${API_WORKERS:-1}
LOG_LEVEL=${LOG_LEVEL:-"info"}

echo "Starting Crypto LLM Analyst..."
echo "Host: $HOST"
echo "Port: $PORT"
echo "Workers: $WORKERS"
echo "Log Level: $LOG_LEVEL"

# Check required environment variables
if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "Warning: OPENAI_API_KEY not set"
fi

if [[ -z "$DATABASE_URL" ]]; then
    echo "Warning: DATABASE_URL not set, using default"
fi

# Start the application
exec uvicorn api.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --log-level "$LOG_LEVEL" \
    --access-log \
    --loop uvloop