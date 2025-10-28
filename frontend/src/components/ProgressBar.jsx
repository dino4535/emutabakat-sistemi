import './ProgressBar.css'

/**
 * Progress Bar Component
 * Upload ve bulk işlemlerde ilerleme gösterir
 */
export default function ProgressBar({ 
  progress = 0,  // 0-100
  color = 'primary', // 'primary', 'success', 'danger', 'warning'
  size = 'medium', // 'small', 'medium', 'large'
  showPercentage = true,
  label = null,
  striped = false,
  animated = false
}) {
  const progressValue = Math.min(100, Math.max(0, progress))
  
  return (
    <div className={`progress-bar-container progress-${size}`}>
      {label && <div className="progress-label">{label}</div>}
      
      <div className="progress-bar-wrapper">
        <div className="progress-bar-track">
          <div 
            className={`
              progress-bar-fill 
              progress-${color}
              ${striped ? 'progress-striped' : ''}
              ${animated ? 'progress-animated' : ''}
            `}
            style={{ width: `${progressValue}%` }}
          >
            {showPercentage && size !== 'small' && (
              <span className="progress-percentage">{progressValue}%</span>
            )}
          </div>
        </div>
        
        {showPercentage && size === 'small' && (
          <span className="progress-percentage-external">{progressValue}%</span>
        )}
      </div>
    </div>
  )
}

// Circular Progress
export function CircularProgress({ 
  progress = 0, 
  size = 120, 
  strokeWidth = 8,
  color = 'primary'
}) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (progress / 100) * circumference

  const colorMap = {
    primary: '#3b82f6',
    success: '#10b981',
    danger: '#ef4444',
    warning: '#f59e0b'
  }

  return (
    <div className="circular-progress" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
        />
        
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colorMap[color] || colorMap.primary}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset 0.3s ease' }}
        />
      </svg>
      
      <div className="circular-progress-text">
        {Math.round(progress)}%
      </div>
    </div>
  )
}

// Step Progress (Multi-step forms için)
export function StepProgress({ steps = [], currentStep = 0 }) {
  return (
    <div className="step-progress">
      {steps.map((step, index) => (
        <div key={index} className="step-item">
          <div className={`
            step-circle 
            ${index < currentStep ? 'step-completed' : ''}
            ${index === currentStep ? 'step-active' : ''}
            ${index > currentStep ? 'step-pending' : ''}
          `}>
            {index < currentStep ? '✓' : index + 1}
          </div>
          
          <div className="step-label">{step}</div>
          
          {index < steps.length - 1 && (
            <div className={`
              step-line 
              ${index < currentStep ? 'step-line-completed' : ''}
            `} />
          )}
        </div>
      ))}
    </div>
  )
}

