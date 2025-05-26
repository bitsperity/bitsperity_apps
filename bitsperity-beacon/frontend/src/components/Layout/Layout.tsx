import { ReactNode, useState } from 'react'
import Header from './Header'
import MobileNav from './MobileNav'
import DesktopSidebar from './DesktopSidebar'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Mobile Navigation */}
      <MobileNav isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      {/* Desktop Sidebar */}
      <DesktopSidebar />
      
      {/* Header */}
      <Header onMenuClick={() => setSidebarOpen(true)} />
      
      {/* Main Content */}
      <main className="lg:pl-72">
        <div className="px-4 sm:px-6 lg:px-8 py-6 pt-20 lg:pt-6">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </div>
      </main>
      
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
} 