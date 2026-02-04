import { memo, useState, useEffect, useRef } from 'react'
import './PerformanceMonitor.css'

const PerformanceMonitor = memo(() => {
  const [fps, setFps] = useState(60)
  const frameCountRef = useRef(0)
  const lastTimeRef = useRef(performance.now())
  const updateIntervalRef = useRef(0)
  
  useEffect(() => {
    let animationFrameId: number
    
    const measurePerformance = () => {
      const now = performance.now()
      frameCountRef.current++
      
      // 每500ms更新一次，提高响应速度
      if (now - updateIntervalRef.current >= 500) {
        const elapsed = now - lastTimeRef.current
        const currentFps = Math.round((frameCountRef.current * 1000) / elapsed)
        setFps(currentFps)
        
        if (typeof window !== 'undefined') {
          (window as any).__KIRO_FPS__ = currentFps
        }
        
        frameCountRef.current = 0
        lastTimeRef.current = now
        updateIntervalRef.current = now
      }
      
      animationFrameId = requestAnimationFrame(measurePerformance)
    }
    
    animationFrameId = requestAnimationFrame(measurePerformance)
    
    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId)
      }
    }
  }, [])
  
  const fpsColor = fps >= 55 ? '#52c41a' : fps >= 30 ? '#faad14' : '#ff4d4f'
  
  return (
    <div className="performance-monitor">
      <div className="perf-metric">
        <span className="perf-label">FPS</span>
        <span className="perf-value" style={{ color: fpsColor }}>{fps}</span>
      </div>
    </div>
  )
})

PerformanceMonitor.displayName = 'PerformanceMonitor'

export default PerformanceMonitor
