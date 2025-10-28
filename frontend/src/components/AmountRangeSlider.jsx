import { useState, useEffect } from 'react'
import './AmountRangeSlider.css'

/**
 * Amount Range Slider Component
 * Miktar aralığı seçimi için dual-thumb slider
 */
export default function AmountRangeSlider({
  min = 0,
  max = 1000000,
  step = 1000,
  minValue,
  maxValue,
  onChange,
  label = "Tutar Aralığı",
  currency = "₺",
  showInputs = true,
  className = ''
}) {
  const [localMin, setLocalMin] = useState(minValue || min)
  const [localMax, setLocalMax] = useState(maxValue || max)

  useEffect(() => {
    setLocalMin(minValue || min)
    setLocalMax(maxValue || max)
  }, [minValue, maxValue, min, max])

  const handleMinChange = (value) => {
    const newMin = Math.min(Number(value), localMax - step)
    setLocalMin(newMin)
    onChange && onChange({ min: newMin, max: localMax })
  }

  const handleMaxChange = (value) => {
    const newMax = Math.max(Number(value), localMin + step)
    setLocalMax(newMax)
    onChange && onChange({ min: localMin, max: newMax })
  }

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('tr-TR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  // Slider yüzdesi hesapla
  const minPercent = ((localMin - min) / (max - min)) * 100
  const maxPercent = ((localMax - min) / (max - min)) * 100

  return (
    <div className={`amount-range-slider ${className}`}>
      {label && <label className="amount-range-label">{label}</label>}
      
      <div className="amount-display">
        <span className="amount-value">
          {currency}{formatAmount(localMin)}
        </span>
        <span className="amount-separator">-</span>
        <span className="amount-value">
          {currency}{formatAmount(localMax)}
        </span>
      </div>

      <div className="slider-container">
        <div className="slider-track">
          <div 
            className="slider-range"
            style={{
              left: `${minPercent}%`,
              width: `${maxPercent - minPercent}%`
            }}
          />
        </div>
        
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={localMin}
          onChange={(e) => handleMinChange(e.target.value)}
          className="slider-thumb slider-thumb-min"
        />
        
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={localMax}
          onChange={(e) => handleMaxChange(e.target.value)}
          className="slider-thumb slider-thumb-max"
        />
      </div>

      {showInputs && (
        <div className="amount-inputs">
          <div className="amount-input-wrapper">
            <label>Min</label>
            <input
              type="number"
              value={localMin}
              onChange={(e) => handleMinChange(e.target.value)}
              min={min}
              max={localMax - step}
              step={step}
            />
          </div>
          
          <div className="amount-input-wrapper">
            <label>Max</label>
            <input
              type="number"
              value={localMax}
              onChange={(e) => handleMaxChange(e.target.value)}
              min={localMin + step}
              max={max}
              step={step}
            />
          </div>
        </div>
      )}
    </div>
  )
}

