import { Button, Input, Select, Table, Tag, Space, Tooltip } from 'antd'
import { DownloadOutlined, ReloadOutlined, GithubOutlined, StarOutlined, UserOutlined, CheckCircleOutlined, CloseCircleOutlined, MailOutlined, LinkOutlined, TwitterOutlined } from '@ant-design/icons'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiService } from '@/services/api'
import { memo, useState, useCallback, useMemo } from 'react'
import type { ColumnsType } from 'antd/es/table'
import './GitHubDataSection.css'

const { Search } = Input
const { Option } = Select

interface GitHubDataSectionProps {
  isActive: boolean
  stats?: any
}

const GitHubDataSection = memo(({ isActive, stats }: GitHubDataSectionProps) => {
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('qualified') // 默认显示合格的
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // 查询数据
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['github-data', currentPage, pageSize, statusFilter],
    queryFn: () => apiService.getPlatformData('github', currentPage, pageSize, statusFilter === 'all' ? undefined : statusFilter),
    enabled: isActive,
    staleTime: 30000,
  })

  // 导出数据
  const exportMutation = useMutation({
    mutationFn: () => apiService.exportData('github', 'xlsx'),
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
      item.username?.toLowerCase().includes(search) ||
      item.bio?.toLowerCase().includes(search)
    )
  }, [data, searchText])

  // 渲染用户信息
  const renderUser = useCallback((text: string, record: any) => (
    <div className="user-cell">
      <div className="user-avatar">
        <GithubOutlined />
      </div>
      <div className="user-info">
        <a 
          href={`https://github.com/${text}`} 
          target="_blank" 
          rel="noopener noreferrer"
          className="user-name"
        >
          {text || '未知用户'}
        </a>
        <div className="user-bio">{record.bio || '暂无简介'}</div>
      </div>
    </div>
  ), [])

  // 渲染联系方式
  const renderContact = useCallback((text: string, record: any) => {
    const contacts = []
    
    if (record.email) {
      contacts.push(
        <div key="email" className="contact-item">
          <MailOutlined />
          <a href={`mailto:${record.email}`} className="contact-link">{record.email}</a>
        </div>
      )
    }
    
    if (record.blog) {
      contacts.push(
        <div key="blog" className="contact-item">
          <LinkOutlined />
          <a href={record.blog} target="_blank" rel="noopener noreferrer" className="contact-link">
            {record.blog.length > 30 ? record.blog.substring(0, 30) + '...' : record.blog}
          </a>
        </div>
      )
    }
    
    if (record.twitter_username) {
      contacts.push(
        <div key="twitter" className="contact-item">
          <TwitterOutlined />
          <a href={`https://twitter.com/${record.twitter_username}`} target="_blank" rel="noopener noreferrer" className="contact-link">
            @{record.twitter_username}
          </a>
        </div>
      )
    }
    
    return contacts.length > 0 ? <div className="contact-cell">{contacts}</div> : <span className="simple-number">-</span>
  }, [])

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
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      width: 200,
      fixed: 'left' as const,
      render: renderUser,
    },
    {
      title: '关注者',
      dataIndex: 'followers',
      key: 'followers',
      width: 110,
      align: 'center' as const,
      sorter: (a: any, b: any) => (a.followers || 0) - (b.followers || 0),
      render: (val: number) => renderMetric(val, <UserOutlined />),
    },
    {
      title: '总星标',
      dataIndex: 'total_stars',
      key: 'total_stars',
      width: 110,
      align: 'center' as const,
      sorter: (a: any, b: any) => (a.total_stars || 0) - (b.total_stars || 0),
      render: (val: number) => renderMetric(val, <StarOutlined />),
    },
    {
      title: '仓库数',
      dataIndex: 'public_repos',
      key: 'public_repos',
      width: 90,
      align: 'center' as const,
      sorter: (a: any, b: any) => (a.public_repos || 0) - (b.public_repos || 0),
      render: (val: number) => <span className="simple-number">{val || 0}</span>,
    },
    {
      title: '联系方式',
      dataIndex: 'email',
      key: 'contact',
      width: 200,
      render: renderContact,
    },
    {
      title: '位置',
      dataIndex: 'location',
      key: 'location',
      width: 120,
      align: 'center' as const,
      render: (location: string) => <span className="simple-number">{location || '-'}</span>,
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
      title: '发现时间',
      dataIndex: 'discovered_at',
      key: 'discovered_at',
      width: 120,
      align: 'center' as const,
      sorter: (a: any, b: any) => {
        const dateA = a.discovered_at ? new Date(a.discovered_at).getTime() : 0
        const dateB = b.discovered_at ? new Date(b.discovered_at).getTime() : 0
        return dateA - dateB
      },
      render: renderDateTime,
    },
  ], [renderUser, renderMetric, renderContact, renderStatus, renderDateTime])

  return (
    <div className="data-tab-container">
      {/* 顶部操作栏 */}
      <div className="data-header-compact">
        <div className="header-left">
          <h2 className="data-title">
            <GithubOutlined /> GitHub 数据
          </h2>
          <div className="stats-inline">
            <span className="stat-item">
              <span className="stat-label">总计</span>
              <span className="stat-value">{stats?.total_developers?.toLocaleString() || 0}</span>
            </span>
            <span className="stat-item">
              <span className="stat-label">合格</span>
              <span className="stat-value success">{stats?.qualified_developers?.toLocaleString() || 0}</span>
            </span>
            <span className="stat-item">
              <span className="stat-label">合格率</span>
              <span className="stat-value">
                {stats?.total_developers ? Math.round((stats.qualified_developers / stats.total_developers) * 100) : 0}%
              </span>
            </span>
          </div>
        </div>
        
        <Space size="small">
          <Search
            placeholder="搜索用户名或简介"
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

GitHubDataSection.displayName = 'GitHubDataSection'

export default GitHubDataSection
