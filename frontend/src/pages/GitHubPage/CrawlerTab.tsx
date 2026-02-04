import { Button, Input, message } from 'antd'
import { PlayCircleOutlined, PauseCircleOutlined, SaveOutlined, PlusOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiService } from '@/services/api'
import { memo, useCallback, useState, useEffect, useMemo, useRef } from 'react'
import OptimizedSlider from '@/components/common/OptimizedSlider'
import VirtualKeywordList from '@/components/common/VirtualKeywordList'
import './GitHubSection.css'

interface GitHubCrawlerSectionProps {
  isActive: boolean
  status?: {
    crawler_running?: boolean
  }
}

const GitHubCrawlerSection = memo(({ isActive, status }: GitHubCrawlerSectionProps) => {
  const queryClient = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  
  // 使用useRef避免重复创建默认值
  const defaultConfig = useRef({
    min_followers: 100,
    min_stars: 100,
    min_repo_stars: 100,
    max_developers_per_run: 300,
    min_delay: 4.0,
    max_delay: 7.0,
    initial_cooldown: 5,
    max_429_backoff: 30,
    academic_min_followers: 50,
    academic_min_stars: 100,
    discovery_buffer_ratio: 1.3,
    max_discovery_per_batch: 50,
    min_discovery_per_batch: 10,
  })
  
  const [config, setConfig] = useState(defaultConfig.current)

  // 关键词状态（可编辑）
  const [keywords, setKeywords] = useState({
    search_keywords: [] as string[],
    core_ai_keywords: [] as string[],
    academic_keywords: [] as string[],
    research_project_keywords: [] as string[],
    exclusion_organizations: [] as string[],
  })

  const [newKeyword, setNewKeyword] = useState({
    search: '',
    core: '',
    academic: '',
    research: '',
    exclusion: '',
  })

  // 缓存爬虫运行状态
  const isRunning = useMemo(() => status?.crawler_running ?? false, [status?.crawler_running])
  
  // 缓存计算值
  const totalKeywords = useMemo(
    () => keywords.search_keywords.length + keywords.core_ai_keywords.length + keywords.academic_keywords.length,
    [keywords.search_keywords.length, keywords.core_ai_keywords.length, keywords.academic_keywords.length]
  )
  
  const totalExclusions = useMemo(
    () => keywords.research_project_keywords.length + keywords.exclusion_organizations.length,
    [keywords.research_project_keywords.length, keywords.exclusion_organizations.length]
  )
  
  // 使用Set优化查重性能
  const keywordSets = useMemo(() => ({
    search: new Set(keywords.search_keywords),
    core: new Set(keywords.core_ai_keywords),
    academic: new Set(keywords.academic_keywords),
    research: new Set(keywords.research_project_keywords),
    exclusion: new Set(keywords.exclusion_organizations),
  }), [keywords.search_keywords, keywords.core_ai_keywords, keywords.academic_keywords, keywords.research_project_keywords, keywords.exclusion_organizations])
  
  // 从localStorage加载 - 优化：只在激活时加载
  useEffect(() => {
    // 只在组件激活时加载
    if (!isActive) return
    
    const loadData = () => {
      try {
        const savedConfig = localStorage.getItem('github_crawler_config')
        if (savedConfig) {
          const parsed = JSON.parse(savedConfig)
          // 合并默认配置，确保所有字段都存在
          setConfig({ ...defaultConfig.current, ...parsed })
        }
      } catch (e) {
        console.error('Failed to load config:', e)
      }
      
      try {
        const savedKeywords = localStorage.getItem('github_keywords')
        if (savedKeywords) {
          setKeywords(JSON.parse(savedKeywords))
        } else {
          // 默认关键词
          setKeywords({
            search_keywords: ['stable diffusion', 'ComfyUI', 'text-to-image', 'text-to-video', 'image generation'],
            core_ai_keywords: ['stable-diffusion', 'diffusion-model', 'controlnet', 'animatediff', 'lora'],
            academic_keywords: ['university', 'college', 'institute', 'research', 'lab'],
            research_project_keywords: ['paper', 'arxiv', 'implementation', 'reproduction', 'research'],
            exclusion_organizations: ['replicate', 'runway', 'midjourney', 'openai', 'anthropic'],
          })
        }
      } catch (e) {
        console.error('Failed to load keywords:', e)
      }
    }
    
    if ('requestIdleCallback' in window) {
      requestIdleCallback(loadData)
    } else {
      setTimeout(loadData, 0)
    }
  }, [isActive])

  // 保存配置
  const saveTimeoutRef = useRef<number>()
  const saveConfig = useCallback(() => {
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }
    
    const doSave = () => {
      try {
        localStorage.setItem('github_crawler_config', JSON.stringify(config))
        localStorage.setItem('github_keywords', JSON.stringify(keywords))
        messageApi.success('✓ 配置已保存')
      } catch (e) {
        console.error('Failed to save:', e)
        messageApi.error('保存失败')
      }
    }
    
    if ('requestIdleCallback' in window) {
      requestIdleCallback(doSave)
    } else {
      setTimeout(doSave, 0)
    }
  }, [config, keywords, messageApi])

  // 更新配置
  const updateConfig = useCallback((key: string, value: any) => {
    setConfig(prev => {
      if (prev[key as keyof typeof prev] === value) {
        return prev
      }
      return { ...prev, [key]: value }
    })
  }, [])

  // 添加关键词
  const addKeyword = useCallback((type: 'search' | 'core' | 'academic' | 'research' | 'exclusion') => {
    const keyword = newKeyword[type].trim()
    if (!keyword) return
    
    if (keywordSets[type].has(keyword)) {
      messageApi.warning('关键词已存在')
      return
    }
    
    const keyMap = {
      search: 'search_keywords',
      core: 'core_ai_keywords',
      academic: 'academic_keywords',
      research: 'research_project_keywords',
      exclusion: 'exclusion_organizations',
    }
    const key = keyMap[type] as keyof typeof keywords
    setKeywords(prev => ({
      ...prev,
      [key]: [...prev[key], keyword]
    }))
    setNewKeyword(prev => ({ ...prev, [type]: '' }))
  }, [newKeyword, keywordSets, messageApi])

  // 删除关键词
  const removeKeyword = useCallback((type: 'search' | 'core' | 'academic' | 'research' | 'exclusion', keyword: string) => {
    const keyMap = {
      search: 'search_keywords',
      core: 'core_ai_keywords',
      academic: 'academic_keywords',
      research: 'research_project_keywords',
      exclusion: 'exclusion_organizations',
    }
    const key = keyMap[type] as keyof typeof keywords
    setKeywords(prev => {
      const filtered = prev[key].filter(k => k !== keyword)
      if (filtered.length === prev[key].length) {
        return prev
      }
      return {
        ...prev,
        [key]: filtered
      }
    })
  }, [])
  
  // Input onChange处理器
  const handleKeywordInputChange = useCallback((type: 'search' | 'core' | 'academic' | 'research' | 'exclusion') => {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setNewKeyword(prev => ({ ...prev, [type]: e.target.value }))
    }
  }, [])
  const startMutation = useMutation({
    mutationFn: () => apiService.startCrawler({
      platform: 'github',
      task_type: 'discovery',
      params: {
        min_followers: config.min_followers,
        min_stars: config.min_stars,
        min_repo_stars: config.min_repo_stars,
        max_developers_per_run: config.max_developers_per_run,
        rate_limit: {
          min_delay: config.min_delay,
          max_delay: config.max_delay,
          initial_cooldown: config.initial_cooldown,
          max_429_backoff: config.max_429_backoff,
        },
        academic_min_followers: config.academic_min_followers,
        academic_min_stars: config.academic_min_stars,
        discovery_strategy: {
          enable_deduplication: true,
          deduplication_scope: 'session',
          discovery_buffer_ratio: config.discovery_buffer_ratio,
          max_discovery_per_batch: config.max_discovery_per_batch,
          min_discovery_per_batch: config.min_discovery_per_batch,
        },
      },
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['status'] })
      messageApi.success('🚀 爬虫已启动')
    },
    onError: (error: any) => {
      messageApi.error(`❌ ${error.message || '启动失败'}`)
    },
  })

  const stopMutation = useMutation({
    mutationFn: apiService.stopCrawler,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['status'] })
      messageApi.success('⏸️ 爬虫已停止')
    },
    onError: (error: any) => {
      messageApi.error(`❌ ${error.message || '停止失败'}`)
    },
  })
  
  // 创建稳定的slider回调
  const handleSliderChange = useCallback((key: string, multiplier: number = 1) => {
    return (val: number) => updateConfig(key, val * multiplier)
  }, [updateConfig])

  return (
    <>
      {contextHolder}
      <div className="github-control-v2">
        {/* 顶部操作栏 */}
        <div className="top-action-bar">
          <div className="bar-left">
            <span className="platform-tag">💻 GitHub Discovery</span>
            <div className={`status-chip ${isRunning ? 'active' : ''}`}>
              <span className="chip-dot"></span>
              {isRunning ? 'Running' : 'Ready'}
            </div>
          </div>
          <div className="bar-right">
            <Button
              icon={<SaveOutlined />}
              onClick={saveConfig}
              disabled={isRunning}
              className="save-button"
            >
              保存
            </Button>
            {isRunning ? (
              <Button
                danger
                size="large"
                icon={<PauseCircleOutlined />}
                onClick={() => stopMutation.mutate()}
                loading={stopMutation.isPending}
                className="main-action-btn stop"
              >
                停止爬虫
              </Button>
            ) : (
              <Button
                type="primary"
                size="large"
                icon={<PlayCircleOutlined />}
                onClick={() => startMutation.mutate()}
                loading={startMutation.isPending}
                className="main-action-btn start"
              >
                启动爬虫
              </Button>
            )}
          </div>
        </div>

        {/* 参数配置区 */}
        <div className="config-layout">
          {/* 左侧：数值参数 */}
          <div className="config-section params-section">
            <div className="section-header">
              <h3>爬虫参数</h3>
              <span className="param-count">13项</span>
            </div>

            <div className="params-grid">
              <ParamCard
                name="最小关注者"
                value={config.min_followers}
                min={10}
                max={1000}
                step={10}
                minLabel="10"
                maxLabel="1k"
                disabled={isRunning}
                onChange={handleSliderChange('min_followers')}
              />
              
              <ParamCard
                name="最小星标数"
                value={config.min_stars}
                min={10}
                max={1000}
                step={10}
                minLabel="10"
                maxLabel="1k"
                disabled={isRunning}
                onChange={handleSliderChange('min_stars')}
              />
              
              <ParamCard
                name="仓库星标"
                value={config.min_repo_stars}
                min={10}
                max={500}
                step={10}
                minLabel="10"
                maxLabel="500"
                disabled={isRunning}
                onChange={handleSliderChange('min_repo_stars')}
              />
              
              <ParamCard
                name="目标开发者数"
                value={config.max_developers_per_run}
                min={50}
                max={1000}
                step={50}
                minLabel="50"
                maxLabel="1k"
                disabled={isRunning}
                onChange={handleSliderChange('max_developers_per_run')}
              />
              
              <ParamCard
                name="最小延迟"
                value={config.min_delay}
                min={1}
                max={15}
                step={0.5}
                minLabel="1s"
                maxLabel="15s"
                suffix="秒"
                disabled={isRunning}
                onChange={handleSliderChange('min_delay')}
                formatter={(val) => `${val.toFixed(1)}秒`}
              />
              
              <ParamCard
                name="最大延迟"
                value={config.max_delay}
                min={1}
                max={15}
                step={0.5}
                minLabel="1s"
                maxLabel="15s"
                suffix="秒"
                disabled={isRunning}
                onChange={handleSliderChange('max_delay')}
                formatter={(val) => `${val.toFixed(1)}秒`}
              />
              
              <ParamCard
                name="初始冷却"
                value={config.initial_cooldown}
                min={1}
                max={30}
                minLabel="1s"
                maxLabel="30s"
                suffix="秒"
                disabled={isRunning}
                onChange={handleSliderChange('initial_cooldown')}
              />
              
              <ParamCard
                name="最大退避"
                value={config.max_429_backoff}
                min={10}
                max={120}
                step={10}
                minLabel="10s"
                maxLabel="120s"
                suffix="秒"
                disabled={isRunning}
                onChange={handleSliderChange('max_429_backoff')}
              />
              
              <ParamCard
                name="学术最小关注者"
                value={config.academic_min_followers}
                min={10}
                max={500}
                step={10}
                minLabel="10"
                maxLabel="500"
                disabled={isRunning}
                onChange={handleSliderChange('academic_min_followers')}
              />
              
              <ParamCard
                name="学术最小星标"
                value={config.academic_min_stars}
                min={10}
                max={500}
                step={10}
                minLabel="10"
                maxLabel="500"
                disabled={isRunning}
                onChange={handleSliderChange('academic_min_stars')}
              />
            </div>

            {/* 发现策略 */}
            <div className="section-header" style={{ marginTop: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3>发现策略</h3>
              </div>
              <span className="param-count">3项</span>
            </div>
            <div className="params-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
              <ParamCard
                name="缓冲比例"
                value={config.discovery_buffer_ratio}
                min={1.0}
                max={2.0}
                step={0.1}
                minLabel="1.0x"
                maxLabel="2.0x"
                disabled={isRunning}
                onChange={handleSliderChange('discovery_buffer_ratio')}
                formatter={(val) => `${val.toFixed(1)}x`}
              />
              
              <ParamCard
                name="最小批次"
                value={config.min_discovery_per_batch}
                min={5}
                max={100}
                step={5}
                minLabel="5"
                maxLabel="100"
                disabled={isRunning}
                onChange={handleSliderChange('min_discovery_per_batch')}
              />
            </div>
            
            <div className="params-grid single-col">
              <ParamCard
                name="最大批次"
                value={config.max_discovery_per_batch}
                min={5}
                max={100}
                step={5}
                minLabel="5"
                maxLabel="100"
                disabled={isRunning}
                onChange={handleSliderChange('max_discovery_per_batch')}
              />
            </div>

            {/* 爬虫统计 */}
            <div className="crawler-stats-modern">
              <div className="stats-header">
                <span className="stats-title">实时统计</span>
                <span className="stats-badge">Live</span>
              </div>
              
              <div className="stats-grid-modern">
                <div className="stat-card-modern primary">
                  <div className="stat-card-bg"></div>
                  <div className="stat-card-content">
                    <span className="stat-label-modern blue">已发现开发者</span>
                    <span className="stat-number blue">--</span>
                  </div>
                </div>

                <div className="stat-card-modern success">
                  <div className="stat-card-bg"></div>
                  <div className="stat-card-content">
                    <span className="stat-label-modern green">合格开发者</span>
                    <span className="stat-number green">--</span>
                  </div>
                </div>

                <div className="stat-card-modern time">
                  <div className="stat-card-bg"></div>
                  <div className="stat-card-content">
                    <span className="stat-label-modern yellow">最后运行</span>
                    <span className="stat-number-small yellow">--</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 右侧：关键词配置 */}
          <div className="config-section keywords-section">
            <div className="section-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3>搜索关键词</h3>
              </div>
              <span className="param-count">{totalKeywords}个</span>
            </div>

            <KeywordGroup
              title="搜索关键词"
              emoji="🔍"
              keywords={keywords.search_keywords}
              count={keywords.search_keywords.length}
              newKeyword={newKeyword.search}
              disabled={isRunning}
              onInputChange={handleKeywordInputChange('search')}
              onAdd={() => addKeyword('search')}
              onRemove={(keyword) => removeKeyword('search', keyword)}
              className="search"
            />

            <KeywordGroup
              title="核心AI关键词"
              emoji="⚡"
              keywords={keywords.core_ai_keywords}
              count={keywords.core_ai_keywords.length}
              newKeyword={newKeyword.core}
              disabled={isRunning}
              onInputChange={handleKeywordInputChange('core')}
              onAdd={() => addKeyword('core')}
              onRemove={(keyword) => removeKeyword('core', keyword)}
              className="core"
            />

            <KeywordGroup
              title="学术关键词"
              emoji="🎓"
              keywords={keywords.academic_keywords}
              count={keywords.academic_keywords.length}
              newKeyword={newKeyword.academic}
              disabled={isRunning}
              onInputChange={handleKeywordInputChange('academic')}
              onAdd={() => addKeyword('academic')}
              onRemove={(keyword) => removeKeyword('academic', keyword)}
              className="academic"
            />

            {/* 排除规则 */}
            <div className="section-header" style={{ marginTop: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3>排除规则</h3>
              </div>
              <span className="param-count">{totalExclusions}个</span>
            </div>

            <KeywordGroup
              title="研究项目关键词"
              emoji="📄"
              keywords={keywords.research_project_keywords}
              count={keywords.research_project_keywords.length}
              newKeyword={newKeyword.research}
              disabled={isRunning}
              onInputChange={handleKeywordInputChange('research')}
              onAdd={() => addKeyword('research')}
              onRemove={(keyword) => removeKeyword('research', keyword)}
              className="research"
            />

            <KeywordGroup
              title="排除组织"
              emoji="🏢"
              keywords={keywords.exclusion_organizations}
              count={keywords.exclusion_organizations.length}
              newKeyword={newKeyword.exclusion}
              disabled={isRunning}
              onInputChange={handleKeywordInputChange('exclusion')}
              onAdd={() => addKeyword('exclusion')}
              onRemove={(keyword) => removeKeyword('exclusion', keyword)}
              className="exclusion"
            />
          </div>
        </div>
      </div>
    </>
  )
})

GitHubCrawlerSection.displayName = 'GitHubCrawlerSection'

// 参数卡片组件
const ParamCard = memo(({ 
  name, 
  value, 
  min, 
  max, 
  step = 1,
  minLabel, 
  maxLabel,
  suffix = '',
  disabled,
  onChange,
  formatter
}: {
  name: string
  value: number
  min: number
  max: number
  step?: number
  minLabel: string
  maxLabel: string
  suffix?: string
  disabled: boolean
  onChange: (val: number) => void
  formatter?: (val: number) => string
}) => {
  const safeValue = isNaN(value) || !isFinite(value) ? min : value
  // 修复：确保displayValue正确显示当前值
  const displayValue = formatter 
    ? formatter(safeValue) 
    : suffix 
      ? `${Math.round(safeValue)}${suffix}` 
      : `${Math.round(safeValue)}`
  
  return (
    <div className="param-card">
      <div className="param-header">
        <span className="param-name">{name}</span>
        <span className="param-current">{displayValue}</span>
      </div>
      <div className="param-slider-wrapper">
        <span className="range-label">{minLabel}</span>
        <OptimizedSlider
          value={safeValue}
          onChange={onChange}
          disabled={disabled}
          min={min}
          max={max}
          step={step}
        />
        <span className="range-label">{maxLabel}</span>
      </div>
    </div>
  )
})
ParamCard.displayName = 'ParamCard'

// 可编辑关键词组组件 - 使用虚拟化列表
const KeywordGroup = memo(({
  title,
  emoji,
  keywords,
  count,
  newKeyword,
  disabled,
  onInputChange,
  onAdd,
  onRemove,
  className
}: {
  title: string
  emoji: string
  keywords: string[]
  count: number
  newKeyword: string
  disabled: boolean
  onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onAdd: () => void
  onRemove: (keyword: string) => void
  className: string
}) => {
  return (
    <div className="keyword-group">
      <div className={`keyword-group-header ${className}`}>
        <span className="priority-badge">{emoji} {title}</span>
        <span className="keyword-count">{count}个</span>
      </div>
      <VirtualKeywordList
        keywords={keywords}
        disabled={disabled}
        onRemove={onRemove}
        className={className}
        maxVisible={30}
      />
      {!disabled && (
        <div className="keyword-input-row">
          <Input
            placeholder={`添加${title.includes('组织') ? '组织名称' : title.includes('项目') ? '排除关键词' : '关键词'}...`}
            value={newKeyword}
            onChange={onInputChange}
            onPressEnter={onAdd}
            className="keyword-input"
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={onAdd}
            className={`add-keyword-btn ${className}`}
          >
            添加
          </Button>
        </div>
      )}
    </div>
  )
})
KeywordGroup.displayName = 'KeywordGroup'

export default GitHubCrawlerSection
