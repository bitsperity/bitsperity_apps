// API Configuration for Bitsperity Beacon Frontend

// Completely static configuration to avoid any build-time issues
export const API_CONFIG = {
  BASE_URL: '/api/v1',
  WS_URL: '/api/v1/ws', // Will be resolved by browser relative to current host
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
}

export default API_CONFIG 