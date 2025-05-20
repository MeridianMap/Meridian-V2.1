#!/bin/bash
# Deployment script for the astrological web application
# This script prepares the application for deployment

# Create deployment directory
echo "Creating deployment directory..."
mkdir -p /home/ubuntu/astro-app/deploy

# Copy backend files
echo "Copying backend files..."
cp -r /home/ubuntu/astro-app/backend /home/ubuntu/astro-app/deploy/

# Create requirements.txt for Python dependencies
echo "Creating requirements.txt..."
cat > /home/ubuntu/astro-app/deploy/requirements.txt << EOL
flask==3.1.0
flask-cors==5.0.1
pyswisseph==2.10.3.2
pytz==2025.2
geopy==2.4.1
EOL

# Create README with instructions
echo "Creating README..."
cat > /home/ubuntu/astro-app/deploy/README.md << EOL
# Astrological Chart Calculator

This application calculates astrological charts based on birth information using Swiss Ephemeris.

## Components

- **Backend**: Flask API that interfaces with Swiss Ephemeris
- **Frontend**: Next.js application for user interface

## Installation

### Backend Setup

1. Install Python dependencies:
   \`\`\`
   pip install -r requirements.txt
   \`\`\`

2. Start the Flask API:
   \`\`\`
   python backend/api.py
   \`\`\`

### Frontend Setup

1. Navigate to the frontend directory:
   \`\`\`
   cd frontend
   \`\`\`

2. Install Node.js dependencies:
   \`\`\`
   npm install
   \`\`\`

3. Start the Next.js development server:
   \`\`\`
   npm run dev
   \`\`\`

## Usage

1. Open your browser and navigate to http://localhost:3000
2. Enter birth information:
   - Date
   - Time
   - Location
   - Timezone
   - House system (defaults to Whole Sign)
3. Click "Generate Chart" to view your astrological chart

## Quick Start

Use the provided start script to launch both backend and frontend:
\`\`\`
./scripts/start.sh
\`\`\`

## Features

- Time conversion to UTC
- Location geocoding to latitude/longitude
- Multiple house system support
- Planetary positions and aspects calculation
- Responsive design for all devices
EOL

# Create a simple start script for the deployment
echo "Creating start script for deployment..."
cat > /home/ubuntu/astro-app/deploy/start.sh << EOL
#!/bin/bash
# Start script for the deployed astrological web application

# Kill any existing processes on ports 5000 and 3000
echo "Checking for existing processes..."
kill \$(lsof -t -i:5000) 2>/dev/null
kill \$(lsof -t -i:3000) 2>/dev/null

# Start the Flask backend
echo "Starting Flask backend..."
cd "\$(dirname "\$0")"
python backend/api.py &
FLASK_PID=\$!
echo "Flask backend started with PID: \$FLASK_PID"

# Wait for Flask to initialize
echo "Waiting for Flask to initialize..."
sleep 3

# Start the Next.js frontend
echo "Starting Next.js frontend..."
cd "\$(dirname "\$0")/frontend"
npm run dev &
NEXT_PID=\$!
echo "Next.js frontend started with PID: \$NEXT_PID"

echo "Application is running!"
echo "- Backend API: http://localhost:5000"
echo "- Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to press Ctrl+C
trap "kill \$FLASK_PID \$NEXT_PID; exit" INT
wait
EOL

# Make the start script executable
chmod +x /home/ubuntu/astro-app/deploy/start.sh

# Copy scripts directory
echo "Copying scripts directory..."
cp -r /home/ubuntu/astro-app/scripts /home/ubuntu/astro-app/deploy/

# Make all scripts executable
chmod +x /home/ubuntu/astro-app/deploy/scripts/*.sh

echo "Deployment preparation complete!"
