import { motion } from 'framer-motion'
import { Button, Progress } from 'antd'
import { RocketOutlined, YoutubeOutlined, GithubOutlined, ThunderboltOutlined, FireOutlined, TrophyOutlined } from '@ant-design/icons'
import CountUp from 'react-countup'
import { memo } from 'react'
import { useNavigate } from 'react-router-dom'
import './HeroSection.css'

interface HeroSectionProps {
  isActive: boolean
  status?: any
  youtubeStats?: any
  githubStats?: any
}

const HeroSection = memo(({ isActive, status, youtubeStats, githubStats }: HeroSectionProps) => {
  const navigate = useNavigate()
  
  const totalData = (youtubeStats?.total_kols || 0) + (githubStats?.total_developers || 0)
  const qualifiedData = (youtubeStats?.qualified_kols || 0) + (githubStats?.qualified_developers || 0)
  const qualifiedRate = totalData > 0 ? Math.round((qualifiedData / totalData) * 100) : 0

  return (
    <div className="hero-modern">
      {/* 背景动画 */}
      <div className="hero-bg">
        <div className="hero-grid"></div>
        <div className="hero-gradient"></div>
      </div>

      <div className="hero-container">
        {/* 顶部标题区 */}
        <motion.div 
          className="hero-header"
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="hero-badge">
            <FireOutlined /> AI 驱动
          </div>
          <h1 className="hero-main-title">
            多平台智能爬虫系统
          </h1>
          <p className="hero-desc">
            自动发现、智能分析、实时追踪全球优质内容创作者
          </p>
        </motion.div>

        {/* 核心数据展示 */}
        <motion.div 
          className="hero-stats-grid"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <div className="stat-card stat-card-total">
            <div className="stat-icon-wrapper">
              <TrophyOutlined className="stat-icon" />
            </div>
            <div className="stat-content">
              <div className="stat-value">
                {isActive && <CountUp end={totalData} duration={2} separator="," />}
              </div>
              <div className="stat-label">总数据量</div>
              <div className="stat-progress">
                <Progress 
                  percent={100} 
                  showInfo={false} 
                  strokeColor={{
                    '0%': '#667eea',
                    '100%': '#764ba2',
                  }}
                  trailColor="rgba(255,255,255,0.1)"
                />
              </div>
            </div>
          </div>

          <div className="stat-card stat-card-qualified">
            <div className="stat-icon-wrapper">
              <ThunderboltOutlined className="stat-icon" />
            </div>
            <div className="stat-content">
              <div className="stat-value">
                {isActive && <CountUp end={qualifiedData} duration={2} separator="," />}
              </div>
              <div className="stat-label">合格数据</div>
              <div className="stat-progress">
                <Progress 
                  percent={qualifiedRate} 
                  showInfo={false} 
                  strokeColor={{
                    '0%': '#52c41a',
                    '100%': '#73d13d',
                  }}
                  trailColor="rgba(255,255,255,0.1)"
                />
              </div>
            </div>
          </div>

          <div className="stat-card stat-card-rate">
            <div className="stat-icon-wrapper">
              <FireOutlined className="stat-icon" />
            </div>
            <div className="stat-content">
              <div className="stat-value">
                {qualifiedRate}%
              </div>
              <div className="stat-label">合格率</div>
              <div className="stat-progress">
                <Progress 
                  percent={qualifiedRate} 
                  showInfo={false} 
                  strokeColor={{
                    '0%': '#faad14',
                    '100%': '#ffc53d',
                  }}
                  trailColor="rgba(255,255,255,0.1)"
                />
              </div>
            </div>
          </div>
        </motion.div>

        {/* 平台卡片 */}
        <motion.div 
          className="platform-grid"
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          <motion.div 
            className="platform-card-modern youtube-card-modern"
            whileHover={{ scale: 1.02, y: -5 }}
            onClick={() => navigate('/youtube/data')}
          >
            <div className="platform-header">
              <div className="platform-icon youtube-icon">
                <YoutubeOutlined />
              </div>
              <div className="platform-title">YouTube</div>
            </div>
            <div className="platform-stats">
              <div className="platform-stat">
                <div className="platform-stat-value">
                  {youtubeStats?.total_kols?.toLocaleString() || 0}
                </div>
                <div className="platform-stat-label">总KOL</div>
              </div>
              <div className="platform-divider"></div>
              <div className="platform-stat">
                <div className="platform-stat-value">
                  {youtubeStats?.qualified_kols?.toLocaleString() || 0}
                </div>
                <div className="platform-stat-label">合格</div>
              </div>
            </div>
            <div className="platform-footer">
              <Button 
                type="text" 
                className="platform-btn"
                onClick={(e) => {
                  e.stopPropagation()
                  navigate('/youtube/data')
                }}
              >
                查看数据 →
              </Button>
            </div>
          </motion.div>

          <motion.div 
            className="platform-card-modern github-card-modern"
            whileHover={{ scale: 1.02, y: -5 }}
            onClick={() => navigate('/github/data')}
          >
            <div className="platform-header">
              <div className="platform-icon github-icon">
                <GithubOutlined />
              </div>
              <div className="platform-title">GitHub</div>
            </div>
            <div className="platform-stats">
              <div className="platform-stat">
                <div className="platform-stat-value">
                  {githubStats?.total_developers?.toLocaleString() || 0}
                </div>
                <div className="platform-stat-label">总开发者</div>
              </div>
              <div className="platform-divider"></div>
              <div className="platform-stat">
                <div className="platform-stat-value">
                  {githubStats?.qualified_developers?.toLocaleString() || 0}
                </div>
                <div className="platform-stat-label">合格</div>
              </div>
            </div>
            <div className="platform-footer">
              <Button 
                type="text" 
                className="platform-btn"
                onClick={(e) => {
                  e.stopPropagation()
                  navigate('/github/data')
                }}
              >
                查看数据 →
              </Button>
            </div>
          </motion.div>
        </motion.div>

        {/* 快速操作 */}
        <motion.div 
          className="hero-actions-modern"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.6 }}
        >
          <Button
            size="large"
            icon={<RocketOutlined />}
            className="action-btn action-btn-primary"
            onClick={() => navigate('/youtube/crawler')}
          >
            启动爬虫
          </Button>
          <Button
            size="large"
            icon={<YoutubeOutlined />}
            className="action-btn action-btn-youtube"
            onClick={() => navigate('/youtube/data')}
          >
            YouTube 数据
          </Button>
          <Button
            size="large"
            icon={<GithubOutlined />}
            className="action-btn action-btn-github"
            onClick={() => navigate('/github/data')}
          >
            GitHub 数据
          </Button>
        </motion.div>

        {/* 系统状态 */}
        <motion.div 
          className="hero-status-modern"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.8 }}
        >
          <div className={`status-indicator ${status?.crawler_running ? 'status-running' : 'status-idle'}`}>
            <motion.div 
              className="status-dot"
              animate={{
                scale: status?.crawler_running ? [1, 1.2, 1] : 1,
              }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
            <span className="status-text">
              {status?.crawler_running ? '系统运行中' : '系统空闲'}
            </span>
          </div>
        </motion.div>
      </div>
    </div>
  )
})

HeroSection.displayName = 'HeroSection'

export default HeroSection
