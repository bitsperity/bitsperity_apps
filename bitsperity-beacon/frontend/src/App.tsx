import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import Layout from './components/Layout/Layout'
import Dashboard from './components/Dashboard/Dashboard'
import RegisterService from './components/Registration/RegisterService'
import { useServiceStore } from './stores/serviceStore'

function App() {
  const { connectWebSocket } = useServiceStore()

  useEffect(() => {
    // Verbinde WebSocket beim App Start
    connectWebSocket()
  }, [connectWebSocket])

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