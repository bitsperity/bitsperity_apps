import { useServiceStore } from '../../stores/serviceStore'

export default function Header() {
  const { connected, services } = useServiceStore()

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-xl font-bold text-gray-900">
                Bitsperity Beacon
              </h1>
            </div>
            <div className="ml-4">
              <span className="text-sm text-gray-500">
                Service Discovery Server
              </span>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">
                Services: {services.length}
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-gray-600">
                {connected ? 'Verbunden' : 'Getrennt'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
} 