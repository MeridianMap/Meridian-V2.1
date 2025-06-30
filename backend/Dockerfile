# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt requirements.lock ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy backend code
COPY . .

# Copy ephemeris files
COPY ephe ./ephe

# Expose port
EXPOSE 5000

# Set environment variable for port
ENV PORT=5000
# Set environment variable for Swiss Ephemeris path
ENV EPHEMERIS_PATH=/app/ephe

# Start the Flask application
CMD ["python", "api.py"]
