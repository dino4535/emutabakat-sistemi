import { FaArrowUp, FaArrowDown, FaMinus } from 'react-icons/fa'
import './TrendIndicator.css'

/**
 * Trend Indicator Component
 * Önceki döneme göre artış/azalış gösterir
 */
export default function TrendIndicator({ 
  value, 
  change, 
  isPositiveBetter = true 
}) {
  if (change === 0 || change === undefined || change === null) {
    return (
      <span className="trend-indicator neutral">
        <FaMinus className="trend-icon" />
        <span className="trend-text">Değişim yok</span>
      </span>
    )
  }

  const isPositive = change > 0
  const isGood = isPositiveBetter ? isPositive : !isPositive
  const percentage = Math.abs(change).toFixed(1)

  return (
    <span className={`trend-indicator ${isGood ? 'positive' : 'negative'}`}>
      {isPositive ? (
        <FaArrowUp className="trend-icon" />
      ) : (
        <FaArrowDown className="trend-icon" />
      )}
      <span className="trend-text">
        {isPositive ? '+' : ''}{change.toFixed(1)}%
      </span>
    </span>
  )
}

