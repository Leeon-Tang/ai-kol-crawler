import { useQuery } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'
import { apiService } from '@/services/api'
import HomePage from './HomePage'
import YouTubePage from './YouTubePage'
import GitHubPage from './GitHubPage'

const Home = () => {
  const location = useLocation()

  // 查询统计数据
  const { data: youtubeStats } = useQuery({
    queryKey: ['statistics', 'youtube'],
    queryFn: () => apiService.getStatistics('youtube'),
    staleTime: 60000,
    refetchInterval: false,
    retry: 1,
    refetchOnWindowFocus: false,
  })

  const { data: githubStats } = useQuery({
    queryKey: ['statistics', 'github'],
    queryFn: () => apiService.getStatistics('github'),
    staleTime: 60000,
    refetchInterval: false,
    retry: 1,
    refetchOnWindowFocus: false,
  })

  const { data: githubAcademicStats } = useQuery({
    queryKey: ['statistics', 'github_academic'],
    queryFn: () => apiService.getStatistics('github_academic'),
    staleTime: 60000,
    refetchInterval: false,
    retry: 1,
    refetchOnWindowFocus: false,
  })

  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: apiService.getStatus,
    staleTime: 10000,
    refetchInterval: 10000,
    retry: 1,
    refetchOnWindowFocus: false,
  })

  // 根据路由显示对应内容
  const renderContent = () => {
    switch (location.pathname) {
      case '/':
        return (
          <HomePage
            isActive={true}
            status={status}
            youtubeStats={youtubeStats}
            githubStats={githubStats}
          />
        )
      case '/youtube/crawler':
        return <YouTubePage tab="crawler" isActive={true} status={status} />
      case '/youtube/data':
        return <YouTubePage tab="data" isActive={true} stats={youtubeStats} />
      case '/github/crawler':
        return <GitHubPage tab="crawler" isActive={true} status={status} />
      case '/github/data':
        return <GitHubPage tab="data" isActive={true} stats={githubStats} />
      case '/github/academic':
        return <GitHubPage tab="academic" isActive={true} stats={githubAcademicStats} />
      default:
        return (
          <HomePage
            isActive={true}
            status={status}
            youtubeStats={youtubeStats}
            githubStats={githubStats}
          />
        )
    }
  }

  return (
    <div className="home-container">
      {renderContent()}
    </div>
  )
}

export default Home
