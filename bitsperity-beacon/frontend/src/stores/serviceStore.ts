import { create } from 'zustand'
import { Service, ServiceStatus } from '../types/service'
import { WebSocketMessage } from '../types/api'
import apiClient from '../utils/api'
import { API_CONFIG } from '../config/api'

interface ServiceStore {
  // State
  services: Service[]
  loading: boolean
  error: string | null
  connected: boolean
  websocket: WebSocket | null
  
  // Actions
  fetchServices: () => Promise<void>
  registerService: (serviceData: any) => Promise<Service>
  updateService: (serviceId: string, updateData: any) => Promise<Service>
  deleteService: (serviceId: string) => Promise<void>
  sendHeartbeat: (serviceId: string, ttl?: number) => Promise<void>
  
  // WebSocket
  connectWebSocket: () => void
  disconnectWebSocket: () => void
  
  // Filters
  filterServices: (filters: {
    type?: string
    status?: ServiceStatus
    search?: string
  }) => Service[]
  
  // Utils
  setError: (error: string | null) => void
  setLoading: (loading: boolean) => void
}

export const useServiceStore = create<ServiceStore>((set, get) => ({
  // Initial State
  services: [],
  loading: false,
  error: null,
  connected: false,
  websocket: null,

  // Actions
  fetchServices: async () => {
    set({ loading: true, error: null })
    try {
      const response = await apiClient.listServices()
      set({ services: response.services, loading: false })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Fehler beim Laden der Services',
        loading: false 
      })
    }
  },

  registerService: async (serviceData) => {
    set({ loading: true, error: null })
    try {
      const service = await apiClient.registerService(serviceData)
      set(state => ({ 
        services: [...state.services, service],
        loading: false 
      }))
      return service
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Fehler beim Registrieren des Services',
        loading: false 
      })
      throw error
    }
  },

  updateService: async (serviceId, updateData) => {
    set({ loading: true, error: null })
    try {
      const updatedService = await apiClient.updateService(serviceId, updateData)
      set(state => ({
        services: state.services.map(service => 
          service.service_id === serviceId ? updatedService : service
        ),
        loading: false
      }))
      return updatedService
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Fehler beim Aktualisieren des Services',
        loading: false 
      })
      throw error
    }
  },

  deleteService: async (serviceId) => {
    set({ loading: true, error: null })
    try {
      await apiClient.deleteService(serviceId)
      set(state => ({
        services: state.services.filter(service => service.service_id !== serviceId),
        loading: false
      }))
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Fehler beim Löschen des Services',
        loading: false 
      })
      throw error
    }
  },

  sendHeartbeat: async (serviceId, ttl) => {
    try {
      const response = await apiClient.sendHeartbeat(serviceId, ttl)
      set(state => ({
        services: state.services.map(service => 
          service.service_id === serviceId 
            ? { ...service, expires_at: response.expires_at, last_heartbeat: response.last_heartbeat }
            : service
        )
      }))
    } catch (error) {
      console.error('Heartbeat failed:', error)
    }
  },

  // WebSocket
  connectWebSocket: () => {
    const wsUrl = API_CONFIG.WS_URL
    
    try {
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        set({ connected: true, websocket: ws })
      }
      
      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          handleWebSocketMessage(message, set, get)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
      
      ws.onclose = () => {
        console.log('WebSocket disconnected')
        set({ connected: false, websocket: null })
        
        // Reconnect after 10 seconds (longer delay for stability)
        setTimeout(() => {
          if (!get().connected) {
            console.log('Attempting WebSocket reconnection...')
            get().connectWebSocket()
          }
        }, 10000)
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        set({ connected: false, websocket: null })
        
        // Don't spam reconnection attempts on error
        setTimeout(() => {
          if (!get().connected) {
            console.log('Retrying WebSocket connection after error...')
            get().connectWebSocket()
          }
        }, 15000)
      }
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
    }
  },

  disconnectWebSocket: () => {
    const { websocket } = get()
    if (websocket) {
      websocket.close()
      set({ connected: false, websocket: null })
    }
  },

  // Filters
  filterServices: (filters) => {
    const { services } = get()
    
    return services.filter(service => {
      if (filters.type && service.type !== filters.type) {
        return false
      }
      
      if (filters.status && service.status !== filters.status) {
        return false
      }
      
      if (filters.search) {
        const search = filters.search.toLowerCase()
        return (
          service.name.toLowerCase().includes(search) ||
          service.host.toLowerCase().includes(search) ||
          service.type.toLowerCase().includes(search) ||
          service.tags.some(tag => tag.toLowerCase().includes(search))
        )
      }
      
      return true
    })
  },

  // Utils
  setError: (error) => set({ error }),
  setLoading: (loading) => set({ loading }),
}))

// WebSocket Message Handler
function handleWebSocketMessage(
  message: WebSocketMessage,
  set: any,
  get: any
) {
  switch (message.type) {
    case 'service_registered':
      if (message.data) {
        set((state: any) => ({
          services: [...state.services, message.data]
        }))
      }
      break
      
    case 'service_updated':
      if (message.data) {
        set((state: any) => ({
          services: state.services.map((service: Service) =>
            service.service_id === message.data.service_id ? message.data : service
          )
        }))
      }
      break
      
    case 'service_deregistered':
      if (message.data?.service_id) {
        set((state: any) => ({
          services: state.services.filter((service: Service) =>
            service.service_id !== message.data.service_id
          )
        }))
      }
      break
      
    case 'service_heartbeat':
      if (message.data?.service_id) {
        set((state: any) => ({
          services: state.services.map((service: Service) =>
            service.service_id === message.data.service_id
              ? { ...service, expires_at: message.data.expires_at }
              : service
          )
        }))
      }
      break
      
    case 'services_cleanup':
      // Refresh services after cleanup
      get().fetchServices()
      break
      
    default:
      console.log('Unknown WebSocket message type:', message.type)
  }
} 