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
- One-click deploy: Connect your repo to Render, and Render will auto-detect `render.yaml`.
- Backend: Python web service, starts with Gunicorn.
- Frontend: Static site, built and published from `frontend/dist`.

## API Reference
- `/api/health` — Health check endpoint, returns `{status: "ok"}`
- `/api/astro` — Main ephemeris/astrocartography endpoint (see docs for details)

## Contributing & Docs
- All documentation is consolidated in `docs/` (MkDocs-ready).
- See `Makefile` for dev/test/build commands.
