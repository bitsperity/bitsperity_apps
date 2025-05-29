import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import Layout from './components/Layout/Layout'
import Dashboard from './components/Dashboard/Dashboard'
import RegisterService from './components/Registration/RegisterService'
import { useServiceStore } from './stores/serviceStore'
import { useThemeStore } from './stores/themeStore'

function App() {
  const { connectWebSocket } = useServiceStore()
  const { isDarkMode } = useThemeStore()

  useEffect(() => {
    // Initialize theme on app start
    if (isDarkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    
    // Connect WebSocket on app start
    connectWebSocket()
  }, [connectWebSocket, isDarkMode])

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/register" element={<RegisterService />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App 