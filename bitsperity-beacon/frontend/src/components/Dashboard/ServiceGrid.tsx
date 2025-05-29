import { Service } from '../../types/service'
import ServiceCard from './ServiceCard'
import { Link } from 'react-router-dom'

interface ServiceGridProps {
  services: Service[]
}

export default function ServiceGrid({ services }: ServiceGridProps) {
  if (services.length === 0) {
    return (
      <div className="text-center py-16 lg:py-24">
        <div className="mx-auto max-w-md">
          <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center">
            <svg className="w-12 h-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-3">
            No Services Found
          </h3>
          <p className="text-gray-600 mb-8 leading-relaxed">
            No services have been registered yet. Register your first service to start monitoring your network.
          </p>
          <div className="space-y-4">
            <Link
              to="/register"
              className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transition-all duration-200"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Register Service
            </Link>
            <div className="text-sm text-gray-500">
              or use the API for automatic registration
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6 lg:mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Found Services ({services.length})
        </h3>
        <p className="text-sm text-gray-600">
          Click on a service card for more details
        </p>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 lg:gap-6">
        {services.map((service) => (
          <ServiceCard key={service.service_id} service={service} />
        ))}
      </div>
    </div>
  )
} 