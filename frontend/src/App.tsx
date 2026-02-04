import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Layout/Sidebar'
import Home from './pages/Home'
import Settings from './pages/SettingsPage'
import { useAppStore } from './stores/useAppStore'
import './App.css'

function App() {
  const sidebarCollapsed = useAppStore((state) => state.sidebarCollapsed)

  return (
    <div className="app-container">
      <Sidebar />
      <div className={`app-content ${sidebarCollapsed ? 'sidebar-collapsed' : 'sidebar-expanded'}`}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/youtube/crawler" element={<Home />} />
          <Route path="/youtube/data" element={<Home />} />
          <Route path="/github/crawler" element={<Home />} />
          <Route path="/github/data" element={<Home />} />
          <Route path="/github/academic" element={<Home />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  )
}

export default App

