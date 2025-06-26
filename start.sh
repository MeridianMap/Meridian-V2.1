#!/bin/bash
# Start script for the deployed astrological web application

# Kill stray processes on $PORT and 5000
echo "Checking for existing processes..."
lsof -ti:$PORT | xargs kill -9 2>/dev/null
lsof -ti:5000 | xargs kill -9 2>/dev/null

# Start backend
echo "Starting Flask backend..."
cd backend
python3 api.py &
cd ..

# Start frontend
echo "Starting frontend..."
cd frontend
npm install
npm run dev
cd ..

echo "Application is running!"
echo "- Backend API: http://localhost:5000"
echo "- Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
trap "kill $FLASK_PID $FRONTEND_PID; exit" INT
wait
