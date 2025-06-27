# syntax=docker/dockerfile:1

# --- Backend build stage ---
FROM python:3.11-slim AS backend-build
WORKDIR /app
COPY backend/requirements.lock backend/requirements.txt ./backend/
RUN pip install --upgrade pip && pip install -r backend/requirements.lock
COPY backend ./backend
COPY backend/ephe ./backend/ephe

# --- Frontend build stage ---
FROM node:18-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend .
RUN npm run build

# --- Final stage ---
FROM python:3.11-slim
WORKDIR /app
COPY --from=backend-build /app/backend ./backend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
EXPOSE 5000
ENV PORT=5000
CMD ["gunicorn", "backend.api:app", "--bind", "0.0.0.0:5000"]
