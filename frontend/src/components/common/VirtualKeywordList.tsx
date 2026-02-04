import { memo, useMemo } from 'react'
import { Tag } from 'antd'

interface VirtualKeywordListProps {
  keywords: string[]
  disabled: boolean
  onRemove: (keyword: string) => void
  className: string
  maxVisible?: number
}

// 虚拟化关键词列表 - 只渲染可见的标签
const VirtualKeywordList = memo(({
  keywords,
  disabled,
  onRemove,
  className,
  maxVisible = 50
}: VirtualKeywordListProps) => {
  // 只渲染前N个标签，其余显示数量
  const visibleKeywords = useMemo(() => {
    return keywords.slice(0, maxVisible)
  }, [keywords, maxVisible])
  
  const hiddenCount = keywords.length - visibleKeywords.length
  
  return (
    <div className="keyword-tags">
      {visibleKeywords.map(keyword => (
        <Tag
          key={keyword}
          closable={!disabled}
          onClose={() => onRemove(keyword)}
          className={`keyword-tag ${className}`}
        >
          {keyword}
        </Tag>
      ))}
      {hiddenCount > 0 && (
        <Tag className={`keyword-tag ${className}`}>
          +{hiddenCount} 更多
        </Tag>
      )}
    </div>
  )
}, (prevProps, nextProps) => {
  // 自定义比较函数
  return (
    prevProps.keywords.length === nextProps.keywords.length &&
    prevProps.disabled === nextProps.disabled &&
    prevProps.className === nextProps.className &&
    prevProps.keywords.every((k, i) => k === nextProps.keywords[i])
  )
})

VirtualKeywordList.displayName = 'VirtualKeywordList'

export default VirtualKeywordList
