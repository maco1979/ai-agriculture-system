import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage.tsx'
import DashboardPage from './pages/DashboardPage.tsx'
import MonitoringPage from './pages/MonitoringPage.tsx'
import DecisionPage from './pages/DecisionPage.tsx'
import EdgeComputingPage from './pages/EdgeComputingPage.tsx'
import BlockchainPage from './pages/BlockchainPage.tsx'
import NotFoundPage from './pages/NotFoundPage.tsx'
import { Layout } from './components/Layout.tsx'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/monitoring" element={<MonitoringPage />} />
          <Route path="/decision" element={<DecisionPage />} />
          <Route path="/edge-computing" element={<EdgeComputingPage />} />
          <Route path="/blockchain" element={<BlockchainPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App