import { useState, useEffect, useRef } from 'react'
import './FPSMonitor.css'

interface FPSMonitorProps {
  collapsed?: boolean
}

const FPSMonitor = ({ collapsed = false }: FPSMonitorProps) => {
  const [fps, setFps] = useState(60)
  const frameCountRef = useRef(0)
  const lastTimeRef = useRef(performance.now())
  const animationFrameRef = useRef<number>()

  useEffect(() => {
    const measureFPS = () => {
      frameCountRef.current++
      const currentTime = performance.now()
      const elapsed = currentTime - lastTimeRef.current

      if (elapsed >= 1000) {
        const currentFPS = Math.round((frameCountRef.current * 1000) / elapsed)
        setFps(currentFPS)
        frameCountRef.current = 0
        lastTimeRef.current = currentTime
      }

      animationFrameRef.current = requestAnimationFrame(measureFPS)
    }

    animationFrameRef.current = requestAnimationFrame(measureFPS)

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [])

  const getFPSColor = () => {
    if (fps >= 55) return '#52c41a'
    if (fps >= 30) return '#faad14'
    return '#ff4d4f'
  }

  return (
    <div className="fps-card">
      <div className="fps-header">
        <div className="fps-value" style={{ color: getFPSColor() }}>
          {fps}
        </div>
        <div className="fps-info">
          <span className="fps-label">FPS</span>
        </div>
      </div>
    </div>
  )
}

export default FPSMonitor
