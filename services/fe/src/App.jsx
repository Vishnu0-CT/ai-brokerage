import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Assistant from './pages/Assistant'
import RiskMonitor from './pages/RiskMonitor'
import Coach from './pages/Coach'
import StrategyBuilder from './pages/StrategyBuilder'
import Trade from './pages/Trade'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/trade" element={<Trade />} />
        <Route path="/assistant" element={<Assistant />} />
        <Route path="/risk" element={<RiskMonitor />} />
        <Route path="/coach" element={<Coach />} />
        <Route path="/strategy" element={<StrategyBuilder />} />
      </Routes>
    </Layout>
  )
}

export default App
