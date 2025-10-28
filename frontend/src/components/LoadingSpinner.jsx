import './LoadingSpinner.css'

/**
 * Loading Spinner Component
 * Farklı boyut ve renklerde loading spinner'lar
 */
export default function LoadingSpinner({ 
  size = 'medium',  // 'small', 'medium', 'large'
  color = 'primary', // 'primary', 'secondary', 'success', 'danger', 'white'
  fullscreen = false,
  text = null
}) {
  const sizeClass = `spinner-${size}`
  const colorClass = `spinner-${color}`

  const spinnerElement = (
    <div className={`loading-spinner ${sizeClass} ${colorClass}`}>
      <div className="spinner"></div>
      {text && <p className="spinner-text">{text}</p>}
    </div>
  )

  if (fullscreen) {
    return (
      <div className="spinner-overlay">
        {spinnerElement}
      </div>
    )
  }

  return spinnerElement
}

// Dots Spinner (Alternatif stil)
export function DotsSpinner({ color = 'primary' }) {
  return (
    <div className={`dots-spinner spinner-${color}`}>
      <div className="dot"></div>
      <div className="dot"></div>
      <div className="dot"></div>
    </div>
  )
}

// Pulse Spinner (Alternatif stil)
export function PulseSpinner({ color = 'primary' }) {
  return (
    <div className={`pulse-spinner spinner-${color}`}>
      <div className="pulse"></div>
    </div>
  )
}

