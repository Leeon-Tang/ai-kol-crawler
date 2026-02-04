import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000, // 减少到10秒
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 添加错误处理
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 静默处理连接错误，避免控制台刷屏
    if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      console.warn('API服务未启动，使用模拟数据')
      // 返回模拟数据
      return Promise.resolve(getMockData(error.config.url))
    }
    console.error('API Error:', error.message)
    return Promise.reject(error)
  }
)

// 模拟数据
const getMockData = (url?: string) => {
  if (url?.includes('/status')) {
    return { crawler_running: false, timestamp: new Date().toISOString() }
  }
  if (url?.includes('/statistics/youtube')) {
    return { total_kols: 12580, qualified_kols: 9856, pending_analysis: 1234, pending_expansions: 1490 }
  }
  if (url?.includes('/statistics/github')) {
    return { total_developers: 8964, qualified_developers: 7234 }
  }
  if (url?.includes('/statistics/twitter')) {
    return { total_users: 5432, qualified_users: 4123 }
  }
  return {}
}

// ============================================
// API 接口定义
// ============================================

export interface Statistics {
  total_kols?: number
  qualified_kols?: number
  pending_analysis?: number
  pending_expansions?: number
  total_developers?: number
  qualified_developers?: number
  total_users?: number
  qualified_users?: number
}

export interface CrawlerStatus {
  crawler_running: boolean
  timestamp: string
}

export interface CrawlerTaskRequest {
  platform: string
  task_type: string
  params?: Record<string, any>
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ============================================
// API 方法
// ============================================

export const apiService = {
  // 健康检查
  healthCheck: () => api.get('/health'),

  // 获取系统状态
  getStatus: (): Promise<CrawlerStatus> => api.get('/status'),

  // 获取统计数据
  getStatistics: (platform: string): Promise<Statistics> =>
    api.get(`/statistics/${platform}`),

  // 获取平台数据
  getPlatformData: (
    platform: string,
    page: number = 1,
    pageSize: number = 20,
    status?: string
  ): Promise<PaginatedData<any>> =>
    api.get(`/data/${platform}`, {
      params: { page, page_size: pageSize, status },
    }),

  // 启动爬虫
  startCrawler: (request: CrawlerTaskRequest) =>
    api.post('/crawler/start', request),

  // 停止爬虫
  stopCrawler: () => api.post('/crawler/stop'),

  // 获取日志
  getLogs: (lines: number = 100) =>
    api.get('/logs', { params: { lines } }),

  // 获取配置
  getConfig: () => api.get('/config'),

  // 更新配置
  updateConfig: (config: Record<string, any>) =>
    api.post('/config', { config }),

  // 导出数据
  exportData: (platform: string, format: string = 'xlsx') =>
    api.post(`/export/${platform}`, null, {
      params: { format },
      responseType: 'blob',
    }),
}

export default api
