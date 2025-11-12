#!/bin/bash
# Entrypoint script to ensure database is initialized

echo "Starting WWHD Backend..."
echo "Database path: /data/app.db"

# Check if /data directory exists and is writable
if [ -d "/data" ]; then
    echo "✅ /data directory exists"
    if [ -w "/data" ]; then
        echo "✅ /data is writable"
    else
        echo "❌ /data is not writable"
    fi
else
    echo "⚠️ /data directory doesn't exist, creating..."
    mkdir -p /data
fi

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port 8000