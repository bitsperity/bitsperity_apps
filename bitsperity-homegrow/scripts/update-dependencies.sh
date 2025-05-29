#!/bin/bash

echo "🚀 Installing WebSocket dependencies for HomeGrow v3..."

# Backend dependencies
echo "📦 Installing backend dependencies..."
npm install --save ws

# Frontend dependencies
echo "📦 Installing frontend dependencies..."
npm install --save-dev svelte-dnd-action

# Update existing dependencies
echo "🔄 Updating existing dependencies..."
npm update

echo "✅ Dependencies installed successfully!"

# Check if service worker exists
if [ ! -f "src/service-worker.js" ]; then
  echo "⚠️  Service Worker not found. Creating basic service worker..."
  
  cat > src/service-worker.js << 'EOF'
import { build, files, version } from '$service-worker';

const CACHE = `cache-${version}`;
const ASSETS = [...build, ...files];

self.addEventListener('install', (event) => {
  console.log('[Service Worker] Install');
});

self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activate');
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  // Basic cache strategy will be implemented
});
EOF
  
  echo "✅ Basic service worker created"
fi

# Check if manifest exists
if [ ! -f "static/manifest.json" ]; then
  echo "⚠️  PWA Manifest not found. Creating manifest..."
  
  cat > static/manifest.json << 'EOF'
{
  "name": "HomeGrow v3",
  "short_name": "HomeGrow",
  "description": "Professional Hydroponic System Management",
  "theme_color": "#3b82f6",
  "background_color": "#ffffff",
  "display": "standalone",
  "orientation": "portrait",
  "scope": "/",
  "start_url": "/",
  "icons": [
    {
      "src": "/favicon.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
EOF
  
  echo "✅ PWA manifest created"
fi

echo "🎉 Update complete! Next steps:"
echo "1. Run 'npm run dev' to start development server"
echo "2. Check NEXT_STEPS.md for implementation guide"
echo "3. Test WebSocket connection in the UI" 