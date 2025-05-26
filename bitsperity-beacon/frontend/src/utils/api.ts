import { Service, ServiceCreate, ServiceUpdate, ServiceListResponse, HeartbeatResponse } from '../types/service'
import { HealthResponse, DiscoveryResponse, ServiceDiscoveryFilter } from '../types/api'
import { API_CONFIG } from '../config/api'

const API_BASE_URL = API_CONFIG.BASE_URL

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error(`API Request failed: ${endpoint}`, error)
      throw error
    }
  }

  // Service Management
  async registerService(serviceData: ServiceCreate): Promise<Service> {
    return this.request<Service>('/services/register', {
      method: 'POST',
      body: JSON.stringify(serviceData),
    })
  }

  async getService(serviceId: string): Promise<Service> {
    return this.request<Service>(`/services/${serviceId}`)
  }

  async updateService(serviceId: string, updateData: ServiceUpdate): Promise<Service> {
    return this.request<Service>(`/services/${serviceId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    })
  }

  async deleteService(serviceId: string): Promise<void> {
    return this.request<void>(`/services/${serviceId}`, {
      method: 'DELETE',
    })
  }

  async sendHeartbeat(serviceId: string, ttl?: number): Promise<HeartbeatResponse> {
    const params = ttl ? `?ttl=${ttl}` : ''
    return this.request<HeartbeatResponse>(`/services/${serviceId}/heartbeat${params}`, {
      method: 'PUT',
    })
  }

  async getServiceStatus(serviceId: string): Promise<Service> {
    return this.request<Service>(`/services/${serviceId}/status`)
  }

  // Service Discovery
  async listServices(params: {
    type?: string
    tags?: string[]
    protocol?: string
    status?: string
    limit?: number
    skip?: number
  } = {}): Promise<ServiceListResponse> {
    const searchParams = new URLSearchParams()
    
    if (params.type) searchParams.append('type', params.type)
    if (params.tags) params.tags.forEach(tag => searchParams.append('tags', tag))
    if (params.protocol) searchParams.append('protocol', params.protocol)
    if (params.status) searchParams.append('status', params.status)
    if (params.limit) searchParams.append('limit', params.limit.toString())
    if (params.skip) searchParams.append('skip', params.skip.toString())

    const query = searchParams.toString()
    return this.request<ServiceListResponse>(`/services/${query ? `?${query}` : ''}`)
  }

  async discoverServices(params: {
    type?: string
    tags?: string[]
    protocol?: string
    status?: string
    limit?: number
    skip?: number
  } = {}): Promise<DiscoveryResponse> {
    const searchParams = new URLSearchParams()
    
    if (params.type) searchParams.append('type', params.type)
    if (params.tags) params.tags.forEach(tag => searchParams.append('tags', tag))
    if (params.protocol) searchParams.append('protocol', params.protocol)
    if (params.status) searchParams.append('status', params.status)
    if (params.limit) searchParams.append('limit', params.limit.toString())
    if (params.skip) searchParams.append('skip', params.skip.toString())

    const query = searchParams.toString()
    return this.request<DiscoveryResponse>(`/services/discover${query ? `?${query}` : ''}`)
  }

  async discoverServicesWithFilter(
    filter: ServiceDiscoveryFilter,
    limit = 50,
    skip = 0
  ): Promise<DiscoveryResponse> {
    const params = new URLSearchParams()
    params.append('limit', limit.toString())
    params.append('skip', skip.toString())

    return this.request<DiscoveryResponse>(`/services/discover?${params}`, {
      method: 'POST',
      body: JSON.stringify(filter),
    })
  }

  // Metadata
  async getServiceTypes(): Promise<string[]> {
    return this.request<string[]>('/services/types')
  }

  async getServiceTags(): Promise<string[]> {
    return this.request<string[]>('/services/tags')
  }

  async getExpiredServices(): Promise<ServiceListResponse> {
    return this.request<ServiceListResponse>('/services/expired')
  }

  // Health
  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health')
  }

  async getReadiness(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/ready')
  }

  async getLiveness(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/live')
  }
}

export const apiClient = new ApiClient()
export default apiClient 