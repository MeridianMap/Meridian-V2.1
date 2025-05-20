#!/bin/bash
# Start script for the deployed astrological web application

# Kill any existing processes on ports 5000 and 3000
echo "Checking for existing processes..."
kill $(lsof -t -i:5000) 2>/dev/null
kill $(lsof -t -i:3000) 2>/dev/null

# Start the Flask backend
echo "Starting Flask backend..."
cd "$(dirname "$0")"
python backend/api.py &
FLASK_PID=$!
echo "Flask backend started with PID: $FLASK_PID"

# Wait for Flask to initialize
echo "Waiting for Flask to initialize..."
sleep 3

# Start the Next.js frontend
echo "Starting Next.js frontend..."
cd "$(dirname "$0")/frontend"
npm run dev &
NEXT_PID=$!
echo "Next.js frontend started with PID: $NEXT_PID"

echo "Application is running!"
echo "- Backend API: http://localhost:5000"
echo "- Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to press Ctrl+C
trap "kill $FLASK_PID $NEXT_PID; exit" INT
wait
