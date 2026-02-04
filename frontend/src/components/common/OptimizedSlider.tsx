import { memo, useState, useCallback, useRef } from 'react'
import { Slider } from 'antd'

interface OptimizedSliderProps {
  value: number
  onChange: (val: number) => void
  disabled?: boolean
  min: number
  max: number
  step?: number
}

// 极致优化的Slider - 使用RAF节流
const OptimizedSlider = memo(({ value, onChange, disabled, min, max, step = 1 }: OptimizedSliderProps) => {
  const [localValue, setLocalValue] = useState(value)
  const rafRef = useRef<number>()
  const timerRef = useRef<number>()

  const handleChange = useCallback((val: number) => {
    setLocalValue(val)
    
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current)
    }
    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }
    
    rafRef.current = requestAnimationFrame(() => {
      timerRef.current = window.setTimeout(() => {
        onChange(val)
      }, 300)
    })
  }, [onChange])

  return (
    <Slider
      value={localValue}
      onChange={handleChange}
      disabled={disabled}
      min={min}
      max={max}
      step={step}
    />
  )
}, (prev, next) => 
  prev.value === next.value &&
  prev.disabled === next.disabled &&
  prev.min === next.min &&
  prev.max === next.max &&
  prev.step === next.step
)

OptimizedSlider.displayName = 'OptimizedSlider'

export default OptimizedSlider
