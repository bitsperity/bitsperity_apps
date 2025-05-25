import { useEffect, useState } from 'react'
import { useServiceStore } from '../../stores/serviceStore'
import ServiceGrid from './ServiceGrid'
import { ServiceStatus } from '../../types/service'

export default function Dashboard() {
  const { services, loading, error, fetchServices } = useServiceStore()
  const [filters, setFilters] = useState({
    type: '',
    status: '' as ServiceStatus | '',
    search: ''
  })

  useEffect(() => {
    fetchServices()
  }, [fetchServices])

  const filteredServices = useServiceStore(state => 
    state.filterServices({
      type: filters.type || undefined,
      status: filters.status || undefined,
      search: filters.search || undefined
    })
  )

  const serviceStats = {
    total: services.length,
    active: services.filter(s => s.status === ServiceStatus.ACTIVE).length,
    inactive: services.filter(s => s.status === ServiceStatus.INACTIVE).length,
    expired: services.filter(s => s.status === ServiceStatus.EXPIRED).length,
    unhealthy: services.filter(s => s.status === ServiceStatus.UNHEALTHY).length,
  }

  if (loading && services.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Lade Services...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Service Dashboard</h1>
          <p className="text-gray-600">Übersicht aller registrierten Services</p>
        </div>
        <button
          onClick={() => fetchServices()}
          className="btn-primary"
          disabled={loading}
        >
          {loading ? 'Aktualisiere...' : 'Aktualisieren'}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="card p-4">
          <div className="text-2xl font-bold text-gray-900">{serviceStats.total}</div>
          <div className="text-sm text-gray-600">Gesamt</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-green-600">{serviceStats.active}</div>
          <div className="text-sm text-gray-600">Aktiv</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-gray-600">{serviceStats.inactive}</div>
          <div className="text-sm text-gray-600">Inaktiv</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-red-600">{serviceStats.expired}</div>
          <div className="text-sm text-gray-600">Abgelaufen</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-yellow-600">{serviceStats.unhealthy}</div>
          <div className="text-sm text-gray-600">Ungesund</div>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Suche
            </label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              placeholder="Service Name, Host, Type..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type
            </label>
            <select
              value={filters.type}
              onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Alle Types</option>
              <option value="iot">IoT</option>
              <option value="mqtt">MQTT</option>
              <option value="http">HTTP</option>
              <option value="api">API</option>
              <option value="database">Database</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value as ServiceStatus | '' }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Alle Status</option>
              <option value={ServiceStatus.ACTIVE}>Aktiv</option>
              <option value={ServiceStatus.INACTIVE}>Inaktiv</option>
              <option value={ServiceStatus.EXPIRED}>Abgelaufen</option>
              <option value={ServiceStatus.UNHEALTHY}>Ungesund</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="text-red-800">
              <strong>Fehler:</strong> {error}
            </div>
          </div>
        </div>
      )}

      {/* Services Grid */}
      <ServiceGrid services={filteredServices} />
    </div>
  )
} 