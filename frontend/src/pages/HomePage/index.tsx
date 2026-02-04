import HeroSection from './HeroSection'
import './Home.css'

interface HomePageProps {
  isActive: boolean
  status?: any
  youtubeStats?: any
  githubStats?: any
  githubAcademicStats?: any
}

const HomePage = ({ isActive, status, youtubeStats, githubStats, githubAcademicStats }: HomePageProps) => {
  return (
    <HeroSection
      isActive={isActive}
      status={status}
      youtubeStats={youtubeStats}
      githubStats={githubStats}
      githubAcademicStats={githubAcademicStats}
    />
  )
}

export default HomePage
