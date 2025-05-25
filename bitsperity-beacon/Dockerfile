# Multi-stage Build für Bitsperity Beacon
FROM python:3.11-slim as backend-builder

WORKDIR /app

# System dependencies für Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code
COPY backend/ .

# Frontend Builder Stage
FROM node:18-alpine as frontend-builder

WORKDIR /app

# Frontend dependencies
COPY frontend/package*.json ./
RUN npm install

# Frontend code und build
COPY frontend/ .
RUN npm run build

# Runtime Stage
FROM python:3.11-slim as runtime

WORKDIR /app

# System dependencies für Runtime
RUN apt-get update && apt-get install -y \
    curl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies von builder stage
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Backend code
COPY --from=backend-builder /app /app/backend

# Frontend build
COPY --from=frontend-builder /app/dist /app/frontend/dist

# Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create directories
RUN mkdir -p /app/data /app/logs /var/log/supervisor

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/health || exit 1

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 