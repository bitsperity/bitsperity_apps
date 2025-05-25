export interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
}

export interface HealthResponse {
  status: string
  version: string
  database: string
  message: string
}

export interface DiscoveryResponse {
  services: Service[]
  total: number
  filters_applied: Record<string, string>
  discovery_method: string
}

export interface WebSocketMessage {
  type: string
  event?: string
  data?: any
  timestamp?: number
  message?: string
  client_id?: string
}

export interface ServiceDiscoveryFilter {
  type?: string
  tags?: string[]
  protocol?: string
  status?: string
}

import { Service } from './service' 