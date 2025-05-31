FROM node:18-alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Set working directory
WORKDIR /app

# Install dependencies first (ALL dependencies for build)
COPY package*.json ./
RUN npm ci

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Remove dev dependencies and clean cache
RUN npm prune --production && npm cache clean --force

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S homegrow -u 1001

# Change ownership of app directory
RUN chown -R homegrow:nodejs /app
USER homegrow

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:80/api/v1/health || exit 1

# Start the application with Node.js adapter
CMD ["node", "build/index.js"] 