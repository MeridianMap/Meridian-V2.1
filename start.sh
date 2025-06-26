#!/bin/bash
# Start script for the deployed astrological web application

# Kill stray processes on $PORT and 5000
echo "Checking for existing processes..."
lsof -ti:$PORT | xargs kill -9 2>/dev/null
lsof -ti:5000 | xargs kill -9 2>/dev/null

# Start backend
echo "Starting Flask backend..."
cd backend
python -m flask run --host=0.0.0.0 --port=5000 &
FLASK_PID=$!
cd ..

# Wait for Flask to initialize
echo "Waiting for Flask to initialize..."
sleep 3

# Start frontend
echo "Starting Next.js frontend..."
cd frontend
npm install
npm run dev &
NEXT_PID=$!
cd ..

echo "Application is running!"
echo "- Backend API: http://localhost:5000"
echo "- Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to press Ctrl+C
trap "kill $FLASK_PID $NEXT_PID; exit" INT
wait
