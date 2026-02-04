import { motion } from 'framer-motion'
import { useEffect } from 'react'
import {
  HomeOutlined,
  YoutubeOutlined,
  GithubOutlined,
  SunOutlined,
  MoonOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useLocation } from 'react-router-dom'
import { apiService } from '@/services/api'
import { useAppStore } from '@/stores/useAppStore'
import FPSMonitor from '@/components/common/FPSMonitor'
import './Sidebar.css'

const Sidebar = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const theme = useAppStore((state) => state.theme)
  const toggleTheme = useAppStore((state) => state.toggleTheme)
  const sidebarCollapsed = useAppStore((state) => state.sidebarCollapsed)
  const toggleSidebar = useAppStore((state) => state.toggleSidebar)

  // 动态设置CSS变量
  useEffect(() => {
    const sidebarWidth = sidebarCollapsed ? '70px' : '220px'
    document.documentElement.style.setProperty('--sidebar-width', sidebarWidth)
  }, [sidebarCollapsed])

  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: apiService.getStatus,
    refetchInterval: 10000,
    retry: 1,
  })

  const navItems = [
    { key: '/', label: '首页', icon: <HomeOutlined />, color: 'home' },
    { key: '/youtube/crawler', label: 'YouTube 爬虫', icon: <YoutubeOutlined />, color: 'youtube' },
    { key: '/youtube/data', label: 'YouTube 数据', icon: <YoutubeOutlined />, color: 'youtube' },
    { key: '/github/crawler', label: 'GitHub 爬虫', icon: <GithubOutlined />, color: 'github' },
    { key: '/github/data', label: 'GitHub 开发者', icon: <GithubOutlined />, color: 'github' },
    { key: '/github/academic', label: 'GitHub 学术', icon: <GithubOutlined />, color: 'github' },
  ]

  return (
    <motion.div
      className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}
      initial={{ x: -220, opacity: 0 }}
      animate={{ 
        x: 0, 
        opacity: 1,
        width: sidebarCollapsed ? '70px' : '220px'
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
    >
      <div className="sidebar-container">
        {/* Logo */}
        <motion.div
          className="sidebar-logo"
          whileHover={{ scale: 1.05 }}
          onClick={() => navigate('/')}
        >
          <div className="logo-content">
            <span className="logo-icon">🚀</span>
            <span className="logo-text">AI Crawler</span>
          </div>
        </motion.div>

        {/* 导航菜单 */}
        <div className="sidebar-nav">
          {navItems.map((item) => (
            <motion.div
              key={item.key}
              className={`nav-item nav-item-${item.color} ${location.pathname === item.key ? 'active' : ''}`}
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate(item.key)}
              title={sidebarCollapsed ? item.label : ''}
            >
              <div className="nav-item-content">
                <span className="nav-icon">{item.icon}</span>
                <span>{item.label}</span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* 底部操作区 */}
        <div className="sidebar-actions">
          {/* FPS监控 */}
          <FPSMonitor collapsed={sidebarCollapsed} />
          
          {/* 状态指示 */}
          <motion.div
            className={`status-card ${status?.crawler_running ? 'running' : 'idle'}`}
            whileHover={{ scale: 1.02 }}
          >
            <div className="status-header">
              <motion.div
                className="status-dot"
                animate={{
                  scale: status?.crawler_running ? [1, 1.2, 1] : 1,
                  boxShadow: status?.crawler_running
                    ? [
                        '0 0 0 0 rgba(82, 196, 26, 0.7)',
                        '0 0 0 8px rgba(82, 196, 26, 0)',
                        '0 0 0 0 rgba(82, 196, 26, 0)',
                      ]
                    : 'none',
                }}
                transition={{ duration: 2, repeat: Infinity }}
              />
              <div className="status-info">
                <span className="status-label">状态</span>
                <span className="status-value">
                  {status?.crawler_running ? '运行中' : '空闲'}
                </span>
              </div>
            </div>
          </motion.div>

          {/* 主题切换 */}
          <motion.div
            className="theme-card"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={toggleTheme}
          >
            <div className="theme-content">
              <div className="theme-icon">
                {theme === 'dark' ? <MoonOutlined /> : <SunOutlined />}
              </div>
              <span className="theme-label">
                {theme === 'dark' ? '深色模式' : '浅色模式'}
              </span>
            </div>
          </motion.div>

          {/* 折叠按钮 */}
          <motion.div
            className="collapse-btn"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleSidebar}
          >
            <div className="collapse-btn-content">
              <span>{sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}</span>
              <span>{sidebarCollapsed ? '' : '收起'}</span>
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  )
}

export default Sidebar
