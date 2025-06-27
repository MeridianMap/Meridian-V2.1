# Meridian V2.1

## Project Summary
Meridian is a modern ephemeris and astrocartography API, providing high-precision planetary and astrological calculations. The backend is powered by Python and Swiss Ephemeris, while the frontend is a fast, interactive React/Vite app for map-based exploration.

## Quick Start (Local)
```sh
# 1. Install backend dependencies
pip install -r backend/requirements.lock
# 2. Start backend
python -m backend.api
# 3. Install frontend dependencies
cd frontend && npm install
# 4. Start frontend
npm run dev
```

## Environment Variables
| Variable                | Default/Example                | Description                       |
|-------------------------|--------------------------------|-----------------------------------|
| VITE_GEOAPIFY_API_KEY   | your_geoapify_api_key_here     | Geoapify API key for geocoding    |

## Render.com Deployment Guide

### Prerequisites
1. Create accounts on:
   - [Render.com](https://render.com)
   - [Geoapify](https://www.geoapify.com) (for location search API)

### Deployment Steps
1. **Fork or clone this repository** to your GitHub account
2. **Connect to Render**: 
   - Sign in to Render.com
   - Click "New +" → "Blueprint"
   - Connect your GitHub repo
   - Render will auto-detect `render.yaml` and deploy both services
3. **Configure Environment Variables**:
   - Frontend service: Add `VITE_GEOAPIFY_API_KEY`
4. **Deploy**: Services will build and deploy automatically

### Architecture
- **Backend**: Docker-based Python web service with Swiss Ephemeris
- **Frontend**: Static site built with Vite, served from `frontend/dist`
- **Health Check**: Available at `/api/health`

## API Reference
- `/api/health` — Health check endpoint, returns `{status: "ok"}`
- `/api/astro` — Main ephemeris/astrocartography endpoint (see docs for details)

## Contributing & Docs
- All documentation is consolidated in `docs/` (MkDocs-ready).
- See `Makefile` for dev/test/build commands.
