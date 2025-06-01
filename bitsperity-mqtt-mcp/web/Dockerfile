# Multi-stage build for MQTT MCP Frontend
FROM node:18-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Create production build directory
RUN mkdir -p /app/dist/public
RUN mkdir -p /app/dist/logs

# Copy source files
COPY . .

# Create optimized production build
RUN cp -r public/* /app/dist/public/
RUN cp server.js /app/dist/

# Production stage
FROM node:18-alpine AS production

# Set NODE_ENV to production
ENV NODE_ENV=production
ENV PORT=8091

# Create app user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S frontend -u 1001

# Set working directory
WORKDIR /app

# Copy package files and install production dependencies
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copy built application
COPY --from=build --chown=frontend:nodejs /app/dist/ ./

# Create logs directory with proper permissions
RUN mkdir -p logs && chown frontend:nodejs logs

# Switch to non-root user
USER frontend

# Expose port
EXPOSE 8091

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "const http = require('http'); \
        const options = { hostname: 'localhost', port: 8091, path: '/health', timeout: 5000 }; \
        const req = http.request(options, (res) => { \
            process.exit(res.statusCode === 200 ? 0 : 1); \
        }); \
        req.on('error', () => process.exit(1)); \
        req.on('timeout', () => process.exit(1)); \
        req.end();"

# Start the application
CMD ["node", "server.js"] 