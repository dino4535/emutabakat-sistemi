import LoadingSpinner, { DotsSpinner } from './LoadingSpinner'
import './LoadingButton.css'

/**
 * Loading Button Component
 * İşlem sırasında loading durumunu gösterir
 */
export default function LoadingButton({ 
  children,
  loading = false,
  disabled = false,
  onClick,
  type = 'button',
  variant = 'primary', // 'primary', 'secondary', 'success', 'danger', 'outline'
  size = 'medium', // 'small', 'medium', 'large'
  fullWidth = false,
  loadingText = null,
  spinnerType = 'spinner', // 'spinner', 'dots'
  icon = null,
  className = ''
}) {
  const isDisabled = disabled || loading

  const handleClick = (e) => {
    if (!isDisabled && onClick) {
      onClick(e)
    }
  }

  return (
    <button
      type={type}
      onClick={handleClick}
      disabled={isDisabled}
      className={`
        loading-button 
        button-${variant} 
        button-${size}
        ${fullWidth ? 'button-full-width' : ''}
        ${loading ? 'button-loading' : ''}
        ${className}
      `}
    >
      {loading && spinnerType === 'spinner' && (
        <div className="button-spinner">
          <div className="spinner-mini"></div>
        </div>
      )}
      
      {loading && spinnerType === 'dots' && (
        <DotsSpinner color={variant === 'outline' || variant === 'secondary' ? 'secondary' : 'white'} />
      )}
      
      {!loading && icon && <span className="button-icon">{icon}</span>}
      
      <span className={`button-text ${loading ? 'button-text-loading' : ''}`}>
        {loading && loadingText ? loadingText : children}
      </span>
    </button>
  )
}

