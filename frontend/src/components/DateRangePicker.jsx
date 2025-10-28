import { FaCalendar } from 'react-icons/fa'
import './DateRangePicker.css'

/**
 * Date Range Picker Component
 * Tarih aralığı seçimi için
 */
export default function DateRangePicker({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  label = "Tarih Aralığı",
  presets = true,
  className = ''
}) {
  // Hazır tarih aralıkları
  const applyPreset = (preset) => {
    const today = new Date()
    const startOfDay = new Date(today.setHours(0, 0, 0, 0))
    let start, end

    switch (preset) {
      case 'today':
        start = end = formatDate(startOfDay)
        break
      case 'yesterday':
        const yesterday = new Date(startOfDay)
        yesterday.setDate(yesterday.getDate() - 1)
        start = end = formatDate(yesterday)
        break
      case 'last7days':
        const last7 = new Date(startOfDay)
        last7.setDate(last7.getDate() - 7)
        start = formatDate(last7)
        end = formatDate(startOfDay)
        break
      case 'last30days':
        const last30 = new Date(startOfDay)
        last30.setDate(last30.getDate() - 30)
        start = formatDate(last30)
        end = formatDate(startOfDay)
        break
      case 'thisMonth':
        const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
        start = formatDate(monthStart)
        end = formatDate(startOfDay)
        break
      case 'lastMonth':
        const lastMonthStart = new Date(today.getFullYear(), today.getMonth() - 1, 1)
        const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0)
        start = formatDate(lastMonthStart)
        end = formatDate(lastMonthEnd)
        break
      case 'thisYear':
        const yearStart = new Date(today.getFullYear(), 0, 1)
        start = formatDate(yearStart)
        end = formatDate(startOfDay)
        break
      default:
        return
    }

    onStartDateChange(start)
    onEndDateChange(end)
  }

  const formatDate = (date) => {
    return date.toISOString().split('T')[0]
  }

  return (
    <div className={`date-range-picker ${className}`}>
      {label && <label className="date-range-label">{label}</label>}
      
      <div className="date-range-inputs">
        <div className="date-input-wrapper">
          <FaCalendar className="date-icon" />
          <input
            type="date"
            value={startDate || ''}
            onChange={(e) => onStartDateChange(e.target.value)}
            max={endDate || undefined}
            placeholder="Başlangıç"
          />
        </div>
        
        <span className="date-separator">→</span>
        
        <div className="date-input-wrapper">
          <FaCalendar className="date-icon" />
          <input
            type="date"
            value={endDate || ''}
            onChange={(e) => onEndDateChange(e.target.value)}
            min={startDate || undefined}
            placeholder="Bitiş"
          />
        </div>
      </div>

      {presets && (
        <div className="date-range-presets">
          <button 
            type="button"
            onClick={() => applyPreset('today')}
            className="preset-btn"
          >
            Bugün
          </button>
          <button 
            type="button"
            onClick={() => applyPreset('yesterday')}
            className="preset-btn"
          >
            Dün
          </button>
          <button 
            type="button"
            onClick={() => applyPreset('last7days')}
            className="preset-btn"
          >
            Son 7 Gün
          </button>
          <button 
            type="button"
            onClick={() => applyPreset('last30days')}
            className="preset-btn"
          >
            Son 30 Gün
          </button>
          <button 
            type="button"
            onClick={() => applyPreset('thisMonth')}
            className="preset-btn"
          >
            Bu Ay
          </button>
          <button 
            type="button"
            onClick={() => applyPreset('lastMonth')}
            className="preset-btn"
          >
            Geçen Ay
          </button>
          <button 
            type="button"
            onClick={() => applyPreset('thisYear')}
            className="preset-btn"
          >
            Bu Yıl
          </button>
        </div>
      )}
    </div>
  )
}

