import { Button, Input, message } from 'antd'
import { PlayCircleOutlined, PauseCircleOutlined, SaveOutlined, PlusOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiService } from '@/services/api'
import { memo, useCallback, useState, useEffect, useMemo, useRef } from 'react'
import PerformanceMonitor from '@/components/common/PerformanceMonitor'
import OptimizedSlider from '@/components/common/OptimizedSlider'
import VirtualKeywordList from '@/components/common/VirtualKeywordList'
import './YouTubeSection.css'

interface YouTubeCrawlerSectionProps {
  isActive: boolean
  status?: {
    crawler_running?: boolean
  }
}

const YouTubeCrawlerSection = memo(({ isActive, status }: YouTubeCrawlerSectionProps) => {
  const queryClient = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  
  // 使用useRef避免重复创建默认值
  const defaultConfig = useRef({
    ai_ratio_threshold: 0.3,
    sample_video_count: 10,
    search_results_per_keyword: 5,
    expand_batch_size: 3,
    expand_recommended_videos: 10,
    update_recent_videos: 10,
    max_qualified_kols: 1000,
    rate_limit_delay: 2,
    max_retries: 3,
    active_days_threshold: 90,
    like_weight: 0.4,
    comment_weight: 0.6,
  })
  
  // 严格对应config.json的参数
  const [config, setConfig] = useState(defaultConfig.current)

  // 关键词状态
  const [keywords, setKeywords] = useState({
    priority_high: [] as string[],
    priority_medium: [] as string[],
    priority_low: [] as string[],
  })

  // 排除规则
  const [exclusionRules, setExclusionRules] = useState({
    course_keywords: [] as string[],
    competitor_names: [] as string[],
  })

  const [newKeyword, setNewKeyword] = useState({ high: '', medium: '', low: '' })
  const [newExclusion, setNewExclusion] = useState({ course: '', competitor: '' })
  
  // 缓存爬虫运行状态
  const isRunning = useMemo(() => status?.crawler_running ?? false, [status?.crawler_running])
  
  // 缓存计算值
  const totalKeywords = useMemo(
    () => keywords.priority_high.length + keywords.priority_medium.length + keywords.priority_low.length,
    [keywords.priority_high.length, keywords.priority_medium.length, keywords.priority_low.length]
  )
  
  const totalExclusions = useMemo(
    () => exclusionRules.course_keywords.length + exclusionRules.competitor_names.length,
    [exclusionRules.course_keywords.length, exclusionRules.competitor_names.length]
  )
  
  // 使用Set优化查重性能
  const keywordSets = useMemo(() => ({
    high: new Set(keywords.priority_high),
    medium: new Set(keywords.priority_medium),
    low: new Set(keywords.priority_low),
  }), [keywords.priority_high, keywords.priority_medium, keywords.priority_low])
  
  const exclusionSets = useMemo(() => ({
    course: new Set(exclusionRules.course_keywords),
    competitor: new Set(exclusionRules.competitor_names),
  }), [exclusionRules.course_keywords, exclusionRules.competitor_names])

  // 从localStorage加载 - 优化为异步加载避免阻塞，并使用防抖
  useEffect(() => {
    // 只在组件激活时加载
    if (!isActive) return
    
    // 使用requestIdleCallback或setTimeout避免阻塞初始渲染
    const loadData = () => {
      try {
        const savedConfig = localStorage.getItem('youtube_crawler_config')
        if (savedConfig) {
          setConfig(JSON.parse(savedConfig))
        }
      } catch (e) {
        console.error('Failed to load config:', e)
      }
      
      try {
        const savedKeywords = localStorage.getItem('youtube_keywords')
        if (savedKeywords) {
          setKeywords(JSON.parse(savedKeywords))
        } else {
          // 默认关键词
          setKeywords({
            priority_high: ['Sora AI', 'Kling AI', 'Veo', 'Runway', 'Seedance'],
            priority_medium: ['ChatGPT', 'Claude', 'Gemini', 'Midjourney', 'DALL-E'],
            priority_low: ['ComfyUI', 'LoRA', 'ControlNet', 'AI Agent', 'Workflow'],
          })
        }
      } catch (e) {
        console.error('Failed to load keywords:', e)
      }

      try {
        const savedExclusions = localStorage.getItem('youtube_exclusions')
        if (savedExclusions) {
          setExclusionRules(JSON.parse(savedExclusions))
        } else {
          // 默认排除规则
          setExclusionRules({
            course_keywords: ['第', '講', '课', 'lecture', 'lesson', '教程'],
            competitor_names: ['replicate', 'runway', 'midjourney', 'openai'],
          })
        }
      } catch (e) {
        console.error('Failed to load exclusions:', e)
      }
    }
    
    // 延迟加载避免阻塞初始渲染
    if ('requestIdleCallback' in window) {
      requestIdleCallback(loadData)
    } else {
      setTimeout(loadData, 0)
    }
  }, [isActive])

  // 保存配置 - 使用防抖和异步存储
  const saveTimeoutRef = useRef<number>()
  const saveConfig = useCallback(() => {
    // 清除之前的定时器
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }
    
    // 使用requestIdleCallback异步保存，避免阻塞UI
    const doSave = () => {
      try {
        localStorage.setItem('youtube_crawler_config', JSON.stringify(config))
        localStorage.setItem('youtube_keywords', JSON.stringify(keywords))
        localStorage.setItem('youtube_exclusions', JSON.stringify(exclusionRules))
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
  }, [config, keywords, exclusionRules, messageApi])

  // 更新配置 - 优化为批量更新
  const updateConfig = useCallback((key: string, value: any) => {
    setConfig(prev => {
      // 避免不必要的更新
      if (prev[key as keyof typeof prev] === value) {
        return prev
      }
      return { ...prev, [key]: value }
    })
  }, [])
  
  // 批量更新配置（用于权重联动）
  const updateConfigBatch = useCallback((updates: Partial<typeof config>) => {
    setConfig(prev => ({ ...prev, ...updates }))
  }, [])

  // 添加关键词 - 使用Set优化查重
  const addKeyword = useCallback((priority: 'high' | 'medium' | 'low') => {
    const keyword = newKeyword[priority].trim()
    if (!keyword) return
    
    // 使用Set快速查重
    if (keywordSets[priority].has(keyword)) {
      messageApi.warning('关键词已存在')
      return
    }
    
    const key = `priority_${priority}` as keyof typeof keywords
    setKeywords(prev => ({
      ...prev,
      [key]: [...prev[key], keyword]
    }))
    setNewKeyword(prev => ({ ...prev, [priority]: '' }))
  }, [newKeyword, keywordSets, messageApi])

  // 删除关键词 - 优化filter性能
  const removeKeyword = useCallback((priority: 'high' | 'medium' | 'low', keyword: string) => {
    const key = `priority_${priority}` as keyof typeof keywords
    setKeywords(prev => {
      const filtered = prev[key].filter(k => k !== keyword)
      // 避免不必要的更新
      if (filtered.length === prev[key].length) {
        return prev
      }
      return {
        ...prev,
        [key]: filtered
      }
    })
  }, [])

  // 添加排除规则 - 使用Set优化查重
  const addExclusion = useCallback((type: 'course' | 'competitor') => {
    const keyword = newExclusion[type].trim()
    if (!keyword) return
    
    const setKey = type === 'course' ? 'course' : 'competitor'
    if (exclusionSets[setKey].has(keyword)) {
      messageApi.warning('规则已存在')
      return
    }
    
    const key = type === 'course' ? 'course_keywords' : 'competitor_names'
    setExclusionRules(prev => ({
      ...prev,
      [key]: [...prev[key], keyword]
    }))
    setNewExclusion(prev => ({ ...prev, [type]: '' }))
  }, [newExclusion, exclusionSets, messageApi])

  // 删除排除规则 - 优化filter性能
  const removeExclusion = useCallback((type: 'course' | 'competitor', keyword: string) => {
    const key = type === 'course' ? 'course_keywords' : 'competitor_names'
    setExclusionRules(prev => {
      const filtered = prev[key].filter(k => k !== keyword)
      // 避免不必要的更新
      if (filtered.length === prev[key].length) {
        return prev
      }
      return {
        ...prev,
        [key]: filtered
      }
    })
  }, [])

  // 启动爬虫
  const startMutation = useMutation({
    mutationFn: () => apiService.startCrawler({
      platform: 'youtube',
      task_type: 'discovery',
      params: {
        ai_ratio_threshold: config.ai_ratio_threshold,
        sample_video_count: config.sample_video_count,
        search_results_per_keyword: config.search_results_per_keyword,
        expand_batch_size: config.expand_batch_size,
        expand_recommended_videos: config.expand_recommended_videos,
        update_recent_videos: config.update_recent_videos,
        max_qualified_kols: config.max_qualified_kols,
        rate_limit_delay: config.rate_limit_delay,
        max_retries: config.max_retries,
        active_days_threshold: config.active_days_threshold,
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
  
  // 创建稳定的slider回调 - 避免每次渲染创建新函数
  const handleSliderChange = useCallback((key: string, multiplier: number = 1) => {
    return (val: number) => updateConfig(key, val * multiplier)
  }, [updateConfig])
  
  // 权重联动处理器
  const handleLikeWeightChange = useCallback((val: number) => {
    const newVal = val / 100
    updateConfigBatch({
      like_weight: newVal,
      comment_weight: 1 - newVal
    })
  }, [updateConfigBatch])
  
  const handleCommentWeightChange = useCallback((val: number) => {
    const newVal = val / 100
    updateConfigBatch({
      comment_weight: newVal,
      like_weight: 1 - newVal
    })
  }, [updateConfigBatch])
  
  // Input onChange处理器
  const handleKeywordInputChange = useCallback((priority: 'high' | 'medium' | 'low') => {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setNewKeyword(prev => ({ ...prev, [priority]: e.target.value }))
    }
  }, [])
  
  const handleExclusionInputChange = useCallback((type: 'course' | 'competitor') => {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setNewExclusion(prev => ({ ...prev, [type]: e.target.value }))
    }
  }, [])

  return (
    <>
      {contextHolder}
      <div className="youtube-control-v2">
        {/* 顶部操作栏 */}
        <div className="top-action-bar">
          <div className="bar-left">
            <span className="platform-tag">🎥 YouTube Discovery</span>
            <div className={`status-chip ${isRunning ? 'active' : ''}`}>
              <span className="chip-dot"></span>
              {isRunning ? 'Running' : 'Ready'}
            </div>
            <PerformanceMonitor />
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
              <span className="param-count">10项</span>
            </div>

            <div className="params-grid">
              <ParamCard
                name="AI内容比例阈值"
                value={config.ai_ratio_threshold * 100}
                min={10}
                max={100}
                step={5}
                minLabel="10%"
                maxLabel="100%"
                disabled={isRunning}
                onChange={handleSliderChange('ai_ratio_threshold', 0.01)}
                formatter={(val) => `${val.toFixed(0)}%`}
              />
              
              <ParamCard
                name="采样视频数量"
                value={config.sample_video_count}
                min={5}
                max={50}
                step={5}
                minLabel="5"
                maxLabel="50"
                disabled={isRunning}
                onChange={handleSliderChange('sample_video_count')}
              />
              
              <ParamCard
                name="每关键词搜索结果"
                value={config.search_results_per_keyword}
                min={1}
                max={20}
                minLabel="1"
                maxLabel="20"
                disabled={isRunning}
                onChange={handleSliderChange('search_results_per_keyword')}
              />
              
              <ParamCard
                name="扩散批次大小"
                value={config.expand_batch_size}
                min={1}
                max={10}
                minLabel="1"
                maxLabel="10"
                disabled={isRunning}
                onChange={handleSliderChange('expand_batch_size')}
              />
              
              <ParamCard
                name="扩散推荐视频数"
                value={config.expand_recommended_videos}
                min={5}
                max={50}
                step={5}
                minLabel="5"
                maxLabel="50"
                disabled={isRunning}
                onChange={handleSliderChange('expand_recommended_videos')}
              />
              
              <ParamCard
                name="更新最近视频数"
                value={config.update_recent_videos}
                min={5}
                max={50}
                step={5}
                minLabel="5"
                maxLabel="50"
                disabled={isRunning}
                onChange={handleSliderChange('update_recent_videos')}
              />
              
              <ParamCard
                name="最大合格KOL数"
                value={config.max_qualified_kols}
                min={100}
                max={10000}
                step={100}
                minLabel="100"
                maxLabel="10k"
                disabled={isRunning}
                onChange={handleSliderChange('max_qualified_kols')}
              />
              
              <ParamCard
                name="速率限制延迟"
                value={config.rate_limit_delay}
                min={1}
                max={10}
                minLabel="1s"
                maxLabel="10s"
                suffix="秒"
                disabled={isRunning}
                onChange={handleSliderChange('rate_limit_delay')}
              />
              
              <ParamCard
                name="最大重试次数"
                value={config.max_retries}
                min={1}
                max={10}
                minLabel="1"
                maxLabel="10"
                disabled={isRunning}
                onChange={handleSliderChange('max_retries')}
              />
              
              <ParamCard
                name="活跃天数阈值"
                value={config.active_days_threshold}
                min={30}
                max={365}
                step={30}
                minLabel="30"
                maxLabel="365"
                suffix="天"
                disabled={isRunning}
                onChange={handleSliderChange('active_days_threshold')}
              />
            </div>

            {/* 互动权重 */}
            <div className="section-header" style={{ marginTop: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3>互动权重</h3>
              </div>
              <span className="param-count">2项</span>
            </div>
            <div className="params-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
              <ParamCard
                name="点赞权重"
                value={config.like_weight * 100}
                min={0}
                max={100}
                step={10}
                minLabel="0%"
                maxLabel="100%"
                disabled={isRunning}
                onChange={handleLikeWeightChange}
                formatter={(val) => `${val.toFixed(0)}%`}
              />
              
              <ParamCard
                name="评论权重"
                value={config.comment_weight * 100}
                min={0}
                max={100}
                step={10}
                minLabel="0%"
                maxLabel="100%"
                disabled={isRunning}
                onChange={handleCommentWeightChange}
                formatter={(val) => `${val.toFixed(0)}%`}
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
                    <span className="stat-label-modern red">已发现频道</span>
                    <span className="stat-number red">--</span>
                  </div>
                </div>

                <div className="stat-card-modern success">
                  <div className="stat-card-bg"></div>
                  <div className="stat-card-content">
                    <span className="stat-label-modern green">合格KOL</span>
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
              title="高优先级"
              emoji="🔥"
              priority="high"
              keywords={keywords.priority_high}
              count={keywords.priority_high.length}
              newKeyword={newKeyword.high}
              disabled={isRunning}
              onInputChange={handleKeywordInputChange('high')}
              onAdd={() => addKeyword('high')}
              onRemove={(keyword) => removeKeyword('high', keyword)}
              className="high"
            />

            <KeywordGroup
              title="中优先级"
              emoji="⚡"
              priority="medium"
              keywords={keywords.priority_medium}
              count={keywords.priority_medium.length}
              newKeyword={newKeyword.medium}
              disabled={isRunning}
              onInputChange={handleKeywordInputChange('medium')}
              onAdd={() => addKeyword('medium')}
              onRemove={(keyword) => removeKeyword('medium', keyword)}
              className="medium"
            />

            <KeywordGroup
              title="低优先级"
              emoji="📌"
              priority="low"
              keywords={keywords.priority_low}
              count={keywords.priority_low.length}
              newKeyword={newKeyword.low}
              disabled={isRunning}
              onInputChange={handleKeywordInputChange('low')}
              onAdd={() => addKeyword('low')}
              onRemove={(keyword) => removeKeyword('low', keyword)}
              className="low"
            />

            {/* 排除规则 */}
            <div className="section-header" style={{ marginTop: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3>排除规则</h3>
              </div>
              <span className="param-count">{totalExclusions}个</span>
            </div>

            <KeywordGroup
              title="课程关键词"
              emoji="🚫"
              priority="exclude"
              keywords={exclusionRules.course_keywords}
              count={exclusionRules.course_keywords.length}
              newKeyword={newExclusion.course}
              disabled={isRunning}
              onInputChange={handleExclusionInputChange('course')}
              onAdd={() => addExclusion('course')}
              onRemove={(keyword) => removeExclusion('course', keyword)}
              className="exclude"
            />

            <KeywordGroup
              title="竞品名称"
              emoji="🏢"
              priority="exclude"
              keywords={exclusionRules.competitor_names}
              count={exclusionRules.competitor_names.length}
              newKeyword={newExclusion.competitor}
              disabled={isRunning}
              onInputChange={handleExclusionInputChange('competitor')}
              onAdd={() => addExclusion('competitor')}
              onRemove={(keyword) => removeExclusion('competitor', keyword)}
              className="exclude"
            />
          </div>
        </div>
      </div>
    </>
  )
})

YouTubeCrawlerSection.displayName = 'YouTubeCrawlerSection'

// 优化：提取参数卡片为独立memo组件
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
  const displayValue = formatter ? formatter(safeValue) : `${safeValue}${suffix}`
  
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

// 优化：提取关键词组为独立memo组件 - 使用虚拟化列表
const KeywordGroup = memo(({
  title,
  emoji,
  priority,
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
  priority: 'high' | 'medium' | 'low' | 'exclude'
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
      <div className={`keyword-group-header ${priority}`}>
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
            placeholder={`添加${title.includes('竞品') ? '竞品名称' : title.includes('课程') ? '排除关键词' : '关键词'}...`}
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

export default YouTubeCrawlerSection
