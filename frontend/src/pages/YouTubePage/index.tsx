import CrawlerTab from './CrawlerTab'
import DataTab from './DataTab'

interface YouTubePageProps {
  tab: 'crawler' | 'data'
  isActive: boolean
  status?: any
  stats?: any
}

const YouTubePage = ({ tab, isActive, status, stats }: YouTubePageProps) => {
  if (tab === 'crawler') {
    return <CrawlerTab isActive={isActive} status={status} />
  }
  return <DataTab isActive={isActive} stats={stats} />
}

export default YouTubePage
