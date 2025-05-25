import { Service } from '../../types/service'
import ServiceCard from './ServiceCard'

interface ServiceGridProps {
  services: Service[]
}

export default function ServiceGrid({ services }: ServiceGridProps) {
  if (services.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-6xl mb-4">📡</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Keine Services gefunden
        </h3>
        <p className="text-gray-600">
          Registriere deinen ersten Service um zu beginnen.
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {services.map((service) => (
        <ServiceCard key={service.service_id} service={service} />
      ))}
    </div>
  )
} 