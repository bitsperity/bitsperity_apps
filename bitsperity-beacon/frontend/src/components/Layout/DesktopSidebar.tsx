import { Link, useLocation } from 'react-router-dom'

const navigation = [
  { 
    name: 'Dashboard', 
    href: '/', 
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v6H8V5z" />
      </svg>
    )
  },
  { 
    name: 'Service registrieren', 
    href: '/register', 
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
      </svg>
    )
  },
]

export default function DesktopSidebar() {
  const location = useLocation()

  return (
    <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
      <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white/80 backdrop-blur-xl border-r border-gray-200/50 px-6 pb-4">
        <div className="flex h-16 shrink-0 items-center">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
              <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Bitsperity
              </h1>
              <p className="text-sm text-gray-500 font-medium">Beacon</p>
            </div>
          </div>
        </div>
        <nav className="flex flex-1 flex-col">
          <ul role="list" className="flex flex-1 flex-col gap-y-7">
            <li>
              <ul role="list" className="-mx-2 space-y-2">
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href
                  return (
                    <li key={item.name}>
                      <Link
                        to={item.href}
                        className={`
                          group flex gap-x-3 rounded-xl p-3 text-sm leading-6 font-semibold transition-all duration-200
                          ${isActive
                            ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-700 shadow-sm ring-1 ring-blue-200/50'
                            : 'text-gray-700 hover:text-blue-700 hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-purple-50/50'
                          }
                        `}
                      >
                        <span className={`${isActive ? 'text-blue-600' : 'text-gray-400 group-hover:text-blue-600'} transition-colors`}>
                          {item.icon}
                        </span>
                        {item.name}
                      </Link>
                    </li>
                  )
                })}
              </ul>
            </li>
            <li className="mt-auto">
              <div className="rounded-xl bg-gradient-to-r from-blue-50 to-purple-50 p-4 border border-blue-200/50">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-blue-500 rounded-lg flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">Service Discovery</p>
                    <p className="text-xs text-gray-500">Aktiv & Bereit</p>
                  </div>
                </div>
              </div>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  )
} 