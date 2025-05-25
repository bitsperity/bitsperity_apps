# HomeGrow v3 - Umbrel App Dockerfile
FROM node:20-alpine AS builder

# Install build dependencies
RUN apk add --no-cache python3 make g++

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:20-alpine AS production

# Install runtime dependencies
RUN apk add --no-cache wget curl

# Create app user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S homegrow -u 1001

# Set working directory
WORKDIR /app

# Copy built application
COPY --from=builder --chown=homegrow:nodejs /app/build ./build
COPY --from=builder --chown=homegrow:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=homegrow:nodejs /app/package.json ./package.json
COPY --from=builder --chown=homegrow:nodejs /app/server ./server

# Create data directory
RUN mkdir -p /app/data && chown homegrow:nodejs /app/data

# Switch to app user
USER homegrow

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Start the application
CMD ["node", "server/index.js"] 