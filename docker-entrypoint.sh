#!/bin/bash
set -e

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Install/update Node.js dependencies if node_modules doesn't exist or package.json changed
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Build Tailwind CSS once before starting watch
echo "Building initial Tailwind CSS..."
npm run tailwind || echo "Warning: Tailwind build failed, continuing..."

# Start Tailwind CSS watch in the background
echo "Starting Tailwind CSS watch (changes will be auto-compiled)..."
npm run tailwind:watch > /tmp/tailwind.log 2>&1 &
TAILWIND_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $TAILWIND_PID 2>/dev/null || true
    exit
}
trap cleanup SIGTERM SIGINT

# Wait a moment for Tailwind to start
sleep 2

# Start Django development server (with auto-reload)
echo "Starting Django development server at http://0.0.0.0:8000"
echo "Code changes will auto-reload, Tailwind CSS changes will auto-compile"
exec python manage.py runserver 0.0.0.0:8000

