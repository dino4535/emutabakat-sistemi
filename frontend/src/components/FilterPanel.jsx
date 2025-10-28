import { useState, useEffect } from 'react'
import { FaFilter, FaTimes, FaChevronDown, FaChevronUp } from 'react-icons/fa'
import './FilterPanel.css'

/**
 * Advanced Filter Panel Component
 * Genişletilebilir filtre paneli
 */
export default function FilterPanel({ 
  children, 
  title = "Filtreler",
  isOpen: controlledIsOpen,
  onToggle,
  defaultOpen = false,
  onClear,
  activeFilterCount = 0,
  className = ''
}) {
  const [internalIsOpen, setInternalIsOpen] = useState(defaultOpen)
  
  // Controlled vs Uncontrolled
  const isOpen = controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen
  const toggleOpen = () => {
    if (onToggle) {
      onToggle(!isOpen)
    } else {
      setInternalIsOpen(!internalIsOpen)
    }
  }

  return (
    <div className={`filter-panel ${isOpen ? 'open' : 'collapsed'} ${className}`}>
      <div className="filter-panel-header" onClick={toggleOpen}>
        <div className="filter-panel-title">
          <FaFilter className="filter-icon" />
          <span>{title}</span>
          {activeFilterCount > 0 && (
            <span className="filter-count-badge">{activeFilterCount}</span>
          )}
        </div>
        
        <div className="filter-panel-actions">
          {activeFilterCount > 0 && onClear && (
            <button
              className="btn-clear-filters"
              onClick={(e) => {
                e.stopPropagation()
                onClear()
              }}
              title="Tüm filtreleri temizle"
            >
              <FaTimes /> Temizle
            </button>
          )}
          <button className="btn-toggle" aria-label="Toggle filters">
            {isOpen ? <FaChevronUp /> : <FaChevronDown />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="filter-panel-content animate-fadeInDown">
          {children}
        </div>
      )}
    </div>
  )
}

/**
 * Filter Group - Filtre grupları için
 */
export function FilterGroup({ label, children, columns = 1, className = '' }) {
  return (
    <div className={`filter-group ${className}`}>
      {label && <label className="filter-group-label">{label}</label>}
      <div className={`filter-group-content columns-${columns}`}>
        {children}
      </div>
    </div>
  )
}

/**
 * Filter Item - Tek bir filtre elemanı için
 */
export function FilterItem({ label, children, fullWidth = false, className = '' }) {
  return (
    <div className={`filter-item ${fullWidth ? 'full-width' : ''} ${className}`}>
      {label && <label className="filter-item-label">{label}</label>}
      {children}
    </div>
  )
}

