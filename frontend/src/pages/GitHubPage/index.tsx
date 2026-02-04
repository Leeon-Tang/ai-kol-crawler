import CrawlerTab from './CrawlerTab'
import DataTab from './DataTab'
import AcademicDataTab from './AcademicDataTab'

interface GitHubPageProps {
  tab: 'crawler' | 'data' | 'academic'
  isActive: boolean
  status?: any
  stats?: any
}

const GitHubPage = ({ tab, isActive, status, stats }: GitHubPageProps) => {
  if (tab === 'crawler') {
    return <CrawlerTab isActive={isActive} status={status} />
  }
  if (tab === 'academic') {
    return <AcademicDataTab isActive={isActive} stats={stats} />
  }
  return <DataTab isActive={isActive} stats={stats} />
}

export default GitHubPage
