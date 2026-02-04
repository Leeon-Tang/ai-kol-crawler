import HeroSection from './HeroSection'
import './Home.css'

interface HomePageProps {
  isActive: boolean
  status?: any
  youtubeStats?: any
  githubStats?: any
}

const HomePage = ({ isActive, status, youtubeStats, githubStats }: HomePageProps) => {
  return (
    <HeroSection
      isActive={isActive}
      status={status}
      youtubeStats={youtubeStats}
      githubStats={githubStats}
    />
  )
}

export default HomePage
