import { Service } from '../../types/service'

interface ServiceDetailsProps {
  service: Service | null
  isOpen: boolean
  onClose: () => void
}

export default function ServiceDetails({ service, isOpen, onClose }: ServiceDetailsProps) {
  if (!isOpen || !service) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Service Details</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <p className="mt-1 text-sm text-gray-900">{service.name}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Type</label>
              <p className="mt-1 text-sm text-gray-900">{service.type}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Host</label>
              <p className="mt-1 text-sm text-gray-900">{service.host}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Port</label>
              <p className="mt-1 text-sm text-gray-900">{service.port}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Protocol</label>
              <p className="mt-1 text-sm text-gray-900">{service.protocol}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Status</label>
              <p className="mt-1 text-sm text-gray-900">{service.status}</p>
            </div>
          </div>

          {service.tags && service.tags.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
              <div className="flex flex-wrap gap-2">
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

          {service.metadata && Object.keys(service.metadata).length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Metadata</label>
              <div className="bg-gray-50 rounded p-3">
                <pre className="text-sm text-gray-900">
                  {JSON.stringify(service.metadata, null, 2)}
                </pre>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Created</label>
              <p className="mt-1 text-sm text-gray-900">
                {new Date(service.created_at).toLocaleString('de-DE')}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Updated</label>
              <p className="mt-1 text-sm text-gray-900">
                {new Date(service.updated_at).toLocaleString('de-DE')}
              </p>
            </div>
            {service.expires_at && (
              <div>
                <label className="block text-sm font-medium text-gray-700">Expires</label>
                <p className="mt-1 text-sm text-gray-900">
                  {new Date(service.expires_at).toLocaleString('de-DE')}
                </p>
              </div>
            )}
            {service.last_heartbeat && (
              <div>
                <label className="block text-sm font-medium text-gray-700">Last Heartbeat</label>
                <p className="mt-1 text-sm text-gray-900">
                  {new Date(service.last_heartbeat).toLocaleString('de-DE')}
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Schließen
          </button>
        </div>
      </div>
    </div>
  )
} 