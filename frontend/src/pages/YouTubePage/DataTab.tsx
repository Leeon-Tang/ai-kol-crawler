import { Button, Input, Select, Table, Tag, Space, Tooltip } from 'antd'
import { DownloadOutlined, ReloadOutlined, YoutubeOutlined, EyeOutlined, HeartOutlined, UserOutlined, CheckCircleOutlined, CloseCircleOutlined, MessageOutlined } from '@ant-design/icons'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiService } from '@/services/api'
import { memo, useState, useCallback, useMemo } from 'react'
import type { ColumnsType } from 'antd/es/table'
import './DataSection.css'

const { Search } = Input
const { Option } = Select

interface YouTubeDataTabProps {
  isActive: boolean
  stats?: any
}

const YouTubeDataTab = memo(({ isActive, stats }: YouTubeDataTabProps) => {
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('qualified') // 默认显示合格的
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // 查询数据
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['youtube-data', currentPage, pageSize, statusFilter],
    queryFn: () => apiService.getPlatformData('youtube', currentPage, pageSize, statusFilter === 'all' ? undefined : statusFilter),
    enabled: isActive,
    staleTime: 30000,
  })

  // 导出数据
  const exportMutation = useMutation({
    mutationFn: () => apiService.exportData('youtube', 'xlsx'),
    onSuccess: () => {
      // 触发下载
    },
  })

  // 过滤数据
  const filteredData = useMemo(() => {
    if (!data?.items) return []
    if (!searchText) return data.items
    
    const search = searchText.toLowerCase()
    return data.items.filter((item: any) => 
      item.channel_name?.toLowerCase().includes(search) ||
      item.channel_id?.toLowerCase().includes(search)
    )
  }, [data, searchText])

  // 渲染频道信息
  const renderChannel = useCallback((text: string, record: any) => (
    <div className="channel-cell">
      <div className="channel-avatar">
        <YoutubeOutlined />
      </div>
      <div className="channel-info">
        <a 
          href={record.channel_url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="channel-name"
        >
          {text || '未知频道'}
        </a>
        <div className="channel-id">{record.channel_id}</div>
      </div>
    </div>
  ), [])

  // 渲染数字指标
  const renderMetric = useCallback((value: number, icon: React.ReactNode, suffix?: string) => (
    <div className="metric-cell">
      <span className="metric-icon">{icon}</span>
      <span className="metric-value">
        {value?.toLocaleString() || 0}
        {suffix && <span className="metric-suffix">{suffix}</span>}
      </span>
    </div>
  ), [])

  // 渲染AI比例
  const renderAIRatio = useCallback((ratio: number, record: any) => {
    const percentage = Math.round((ratio || 0) * 100)
    let colorClass = 'low'
    if (percentage >= 80) colorClass = 'high'
    else if (percentage >= 50) colorClass = 'medium'
    
    return (
      <Tooltip title={`AI视频: ${record.ai_videos || 0} / 已分析: ${record.analyzed_videos || 0}`}>
        <div className={`ai-ratio-cell ${colorClass}`}>
          <div className="ratio-bar">
            <div className="ratio-fill" style={{ width: `${percentage}%` }} />
          </div>
          <span className="ratio-text">{percentage}%</span>
        </div>
      </Tooltip>
    )
  }, [])

  // 渲染状态
  const renderStatus = useCallback((status: string) => {
    const statusConfig: Record<string, { icon: React.ReactNode; text: string; color: string }> = {
      qualified: { icon: <CheckCircleOutlined />, text: '合格', color: 'success' },
      rejected: { icon: <CloseCircleOutlined />, text: '拒绝', color: 'error' },
    }
    const config = statusConfig[status] || { icon: <CheckCircleOutlined />, text: status, color: 'default' }
    
    return (
      <Tag icon={config.icon} color={config.color} className="status-tag-compact">
        {config.text}
      </Tag>
    )
  }, [])

  // 渲染日期时间（精确到秒）
  const renderDateTime = useCallback((dateStr: string) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return (
      <span className="date-text">
        {date.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        })}
      </span>
    )
  }, [])

  // 表格列定义 - 展示所有关键指标
  const columns: ColumnsType<any> = useMemo(() => [
    {
      title: '频道',
      dataIndex: 'channel_name',
      key: 'channel_name',
      width: 200,
      fixed: 'left' as const,
      render: renderChannel,
    },
    {
      title: '订阅数',
      dataIndex: 'subscribers',
      key: 'subscribers',
      width: 110,
      align: 'center' as const,
      sorter: (a: any, b: any) => (a.subscribers || 0) - (b.subscribers || 0),
      render: (val: number) => renderMetric(val, <UserOutlined />),
    },
    {
      title: 'AI比例',
      dataIndex: 'ai_ratio',
      key: 'ai_ratio',
      width: 130,
      align: 'center' as const,
      sorter: (a: any, b: any) => (a.ai_ratio || 0) - (b.ai_ratio || 0),
      render: renderAIRatio,
    },
    {
      title: '平均观看',
      dataIndex: 'avg_views',
      key: 'avg_views',
      width: 110,
      align: 'center' as const,
      sorter: (a: any, b: any) => (a.avg_views || 0) - (b.avg_views || 0),
      render: (val: number) => renderMetric(val, <EyeOutlined />),
    },
    {
      title: '平均点赞',
      dataIndex: 'avg_likes',
      key: 'avg_likes',
      width: 110,
      align: 'center' as const,
      sorter: (a: any, b: any) => (a.avg_likes || 0) - (b.avg_likes || 0),
      render: (val: number) => renderMetric(val, <HeartOutlined />),
    },
    {
      title: '平均评论',
      dataIndex: 'avg_comments',
      key: 'avg_comments',
      width: 110,
      align: 'center' as const,
      sorter: (a: any, b: any) => (a.avg_comments || 0) - (b.avg_comments || 0),
      render: (val: number) => renderMetric(val, <MessageOutlined />),
    },
    {
      title: '互动率',
      dataIndex: 'engagement_rate',
      key: 'engagement_rate',
      width: 90,
      align: 'center' as const,
      sorter: (a: any, b: any) => (a.engagement_rate || 0) - (b.engagement_rate || 0),
      render: (val: number) => <span className="simple-number">{val?.toFixed(2) || 0}%</span>,
    },
    {
      title: '视频数',
      dataIndex: 'total_videos',
      key: 'total_videos',
      width: 80,
      align: 'center' as const,
      sorter: (a: any, b: any) => (a.total_videos || 0) - (b.total_videos || 0),
      render: (val: number) => <span className="simple-number">{val || 0}</span>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      align: 'center' as const,
      filters: [
        { text: '合格', value: 'qualified' },
        { text: '拒绝', value: 'rejected' },
      ],
      render: renderStatus,
    },
    {
      title: '更新时间',
      dataIndex: 'last_updated',
      key: 'last_updated',
      width: 120,
      align: 'center' as const,
      sorter: (a: any, b: any) => {
        const dateA = a.last_updated ? new Date(a.last_updated).getTime() : 0
        const dateB = b.last_updated ? new Date(b.last_updated).getTime() : 0
        return dateA - dateB
      },
      render: renderDateTime,
    },
  ], [renderChannel, renderMetric, renderAIRatio, renderStatus, renderDateTime])

  return (
    <div className="data-tab-container">
      {/* 顶部操作栏 */}
      <div className="data-header-compact">
        <div className="header-left">
          <h2 className="data-title">
            <YoutubeOutlined /> YouTube 数据
          </h2>
          <div className="stats-inline">
            <span className="stat-item">
              <span className="stat-label">总计</span>
              <span className="stat-value">{stats?.total_kols?.toLocaleString() || 0}</span>
            </span>
            <span className="stat-item">
              <span className="stat-label">合格</span>
              <span className="stat-value success">{stats?.qualified_kols?.toLocaleString() || 0}</span>
            </span>
            <span className="stat-item">
              <span className="stat-label">合格率</span>
              <span className="stat-value">
                {stats?.total_kols ? Math.round((stats.qualified_kols / stats.total_kols) * 100) : 0}%
              </span>
            </span>
          </div>
        </div>
        
        <Space size="small">
          <Search
            placeholder="搜索频道名称或ID"
            allowClear
            style={{ width: 220 }}
            onSearch={setSearchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
          
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 100 }}
          >
            <Option value="all">全部状态</Option>
            <Option value="qualified">合格</Option>
            <Option value="rejected">拒绝</Option>
          </Select>
          
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            loading={isLoading}
          >
            刷新
          </Button>
          
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => exportMutation.mutate()}
            loading={exportMutation.isPending}
          >
            导出
          </Button>
        </Space>
      </div>

      {/* 数据表格 */}
      <div className="data-table-wrapper">
        <Table
          columns={columns}
          dataSource={filteredData}
          rowKey="id"
          loading={isLoading}
          scroll={{ x: 1150, y: '100%' }}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: data?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, size) => {
              setCurrentPage(page)
              setPageSize(size)
            },
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          size="middle"
        />
      </div>
    </div>
  )
})

YouTubeDataTab.displayName = 'YouTubeDataTab'

export default YouTubeDataTab
