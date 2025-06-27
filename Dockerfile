# syntax=docker/dockerfile:1

# --- Backend build stage ---
FROM python:3.11-slim AS backend-build

# Install system dependencies for Swiss Ephemeris and other packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    git \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt backend/requirements.lock ./backend/
RUN pip install --upgrade pip && \
    pip install -r backend/requirements.txt

# Copy backend source code
COPY backend ./backend

# Copy ephemeris data if it exists
COPY backend/ephe ./backend/ephe

# --- Frontend build stage ---
FROM node:18-slim AS frontend-build

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --only=production

# Copy frontend source and build
COPY frontend .
RUN npm run build

# --- Final production stage ---
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies from build stage
COPY --from=backend-build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-build /usr/local/bin /usr/local/bin

# Copy backend application
COPY --from=backend-build /app/backend ./backend

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port (will be overridden by Render)
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/api/health || exit 1

# Start command (using gunicorn for production)
CMD ["sh", "-c", "cd backend && gunicorn api:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 60"]
