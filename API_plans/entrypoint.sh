#!/bin/bash
echo "🚀 Starting API Plans initialization..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
python init_database.py

if [ $? -eq 0 ]; then
    echo "✅ Database connection successful! Starting server..."
    exec uvicorn main:app --host 0.0.0.0 --port 8001 --reload
else
    echo "❌ Database connection failed. Exiting..."
    exit 1
fi