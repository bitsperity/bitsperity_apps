export interface Service {
  service_id: string
  name: string
  type: string
  host: string
  port: number
  protocol: string
  tags: string[]
  metadata: Record<string, string>
  status: ServiceStatus
  ttl: number
  expires_at: string
  last_heartbeat?: string
  created_at: string
  updated_at: string
  health_check_url?: string
  health_check_interval?: number
  mdns_service_type?: string
}

export enum ServiceStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  EXPIRED = 'expired',
  UNHEALTHY = 'unhealthy'
}

export interface ServiceCreate {
  name: string
  type: string
  host: string
  port: number
  protocol?: string
  tags?: string[]
  metadata?: Record<string, string>
  ttl?: number
  health_check_url?: string
  health_check_interval?: number
}

export interface ServiceUpdate {
  name?: string
  type?: string
  host?: string
  port?: number
  protocol?: string
  tags?: string[]
  metadata?: Record<string, string>
  health_check_url?: string
  health_check_interval?: number
}

export interface ServiceListResponse {
  services: Service[]
  total: number
  page: number
  page_size: number
}

export interface HeartbeatResponse {
  service_id: string
  status: ServiceStatus
  expires_at: string
  last_heartbeat: string
  message: string
} 