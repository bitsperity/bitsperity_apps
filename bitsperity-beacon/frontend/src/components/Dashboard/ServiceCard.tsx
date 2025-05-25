import { Service, ServiceStatus } from '../../types/service'
import { useServiceStore } from '../../stores/serviceStore'

interface ServiceCardProps {
  service: Service
}

export default function ServiceCard({ service }: ServiceCardProps) {
  const { sendHeartbeat, deleteService } = useServiceStore()

  const getStatusColor = (status: ServiceStatus) => {
    switch (status) {
      case ServiceStatus.ACTIVE:
        return 'bg-green-100 text-green-800'
      case ServiceStatus.INACTIVE:
        return 'bg-gray-100 text-gray-800'
      case ServiceStatus.EXPIRED:
        return 'bg-red-100 text-red-800'
      case ServiceStatus.UNHEALTHY:
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'mqtt':
        return '📨'
      case 'http':
      case 'https':
        return '🌐'
      case 'iot':
        return '🔌'
      case 'api':
        return '⚡'
      case 'database':
        return '🗄️'
      default:
        return '📡'
    }
  }

  const handleHeartbeat = async () => {
    try {
      await sendHeartbeat(service.service_id)
    } catch (error) {
      console.error('Heartbeat failed:', error)
    }
  }

  const handleDelete = async () => {
    if (window.confirm(`Service "${service.name}" wirklich löschen?`)) {
      try {
        await deleteService(service.service_id)
      } catch (error) {
        console.error('Delete failed:', error)
      }
    }
  }

  return (
    <div className="card p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{getTypeIcon(service.type)}</span>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {service.name}
            </h3>
            <p className="text-sm text-gray-600">
              {service.host}:{service.port}
            </p>
          </div>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(service.status)}`}>
          {service.status}
        </span>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Type:</span>
          <span className="font-medium">{service.type}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Protocol:</span>
          <span className="font-medium">{service.protocol}</span>
        </div>
        {service.expires_at && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Expires:</span>
            <span className="font-medium">
              {new Date(service.expires_at).toLocaleString('de-DE')}
            </span>
          </div>
        )}
      </div>

      {service.tags && service.tags.length > 0 && (
        <div className="mb-4">
          <div className="flex flex-wrap gap-1">
            {service.tags.map((tag) => (
              <span
                key={tag}
                className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="flex space-x-2">
        <button
          onClick={handleHeartbeat}
          className="flex-1 px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          💓 Heartbeat
        </button>
        <button
          onClick={handleDelete}
          className="px-3 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          🗑️
        </button>
      </div>
    </div>
  )
} 