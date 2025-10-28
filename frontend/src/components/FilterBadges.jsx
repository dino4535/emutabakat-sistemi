import { FaTimes } from 'react-icons/fa'
import './FilterBadges.css'

/**
 * Filter Badges Component
 * Aktif filtreleri badge olarak gösterir
 */
export default function FilterBadges({ filters, onRemove, onClearAll, className = '' }) {
  if (!filters || filters.length === 0) {
    return null
  }

  return (
    <div className={`filter-badges ${className}`}>
      <div className="filter-badges-header">
        <span className="filter-badges-title">Aktif Filtreler:</span>
        {filters.length > 1 && (
          <button 
            className="btn-clear-all-badges"
            onClick={onClearAll}
            title="Tüm filtreleri temizle"
          >
            Tümünü Temizle
          </button>
        )}
      </div>

      <div className="filter-badges-list">
        {filters.map((filter, index) => (
          <FilterBadge
            key={filter.key || index}
            label={filter.label}
            value={filter.value}
            onRemove={() => onRemove(filter.key || index)}
          />
        ))}
      </div>
    </div>
  )
}

/**
 * Single Filter Badge
 */
function FilterBadge({ label, value, onRemove }) {
  return (
    <div className="filter-badge animate-scaleIn">
      <span className="filter-badge-label">{label}:</span>
      <span className="filter-badge-value">{value}</span>
      <button 
        className="filter-badge-remove"
        onClick={onRemove}
        title="Filtreyi kaldır"
      >
        <FaTimes />
      </button>
    </div>
  )
}

