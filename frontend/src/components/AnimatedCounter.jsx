import { useState, useEffect, useRef } from 'react'
import './AnimatedCounter.css'

/**
 * Animated Counter Component
 * Sayıları yumuşak bir şekilde artırarak gösterir
 */
export default function AnimatedCounter({ 
  value, 
  duration = 1000, 
  decimals = 0,
  prefix = '',
  suffix = ''
}) {
  const [count, setCount] = useState(0)
  const countRef = useRef(0)
  const rafRef = useRef(null)

  useEffect(() => {
    const targetValue = Number(value) || 0
    const startValue = countRef.current
    const startTime = performance.now()

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)

      // Easing function (easeOutCubic)
      const easeOutCubic = 1 - Math.pow(1 - progress, 3)
      
      const currentValue = startValue + (targetValue - startValue) * easeOutCubic
      
      countRef.current = currentValue
      setCount(currentValue)

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate)
      } else {
        setCount(targetValue)
        countRef.current = targetValue
      }
    }

    rafRef.current = requestAnimationFrame(animate)

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
      }
    }
  }, [value, duration])

  const formattedValue = count.toFixed(decimals)

  return (
    <span className="animated-counter">
      {prefix}{formattedValue}{suffix}
    </span>
  )
}

