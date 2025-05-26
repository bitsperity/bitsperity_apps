# Bitsperity Beacon - Multi-stage build with proper CSS compilation
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend with proper Tailwind compilation
RUN npm run build

# Python backend stage
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Backend code
COPY backend/ ./backend/

# Frontend (properly built)
COPY --from=frontend-builder /app/frontend/dist/ ./frontend/dist/

# Create directories and set permissions
RUN mkdir -p /app/data /app/logs \
    && chown -R 1000:1000 /app \
    && chmod -R 755 /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BEACON_PORT=80 \
    BEACON_HOST=0.0.0.0

# Switch to non-root user
USER 1000:1000

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:80/api/v1/health || exit 1

# Start FastAPI directly on port 80
WORKDIR /app/backend
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"] 