// API Configuration for Bitsperity Beacon Frontend

// Determine the correct API base URL based on environment
const getApiBaseUrl = (): string => {
  // In production (Umbrel), use the same host and port as the current page
  if (window.location.hostname === 'umbrel.local' || window.location.hostname.includes('umbrel')) {
    return `${window.location.protocol}//${window.location.host}/api/v1`
  }
  
  // For development or other environments
  return '/api/v1'
}

// Determine the correct WebSocket URL
const getWebSocketUrl = (): string => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  
  // In production (Umbrel), use the same host and port as the current page
  // This will be handled by the nginx proxy
  return `${protocol}//${window.location.host}/api/v1/ws`
}

export const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  WS_URL: getWebSocketUrl(),
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
}

export default API_CONFIG 