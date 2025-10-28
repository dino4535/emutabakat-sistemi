import React, { useState } from 'react';
import './Tooltip.css';

/**
 * Tooltip Component
 * Hover/Focus ile açıklama gösterme
 * 
 * @param {React.Node} children - Tooltip'in bağlı olduğu element
 * @param {string} content - Tooltip içeriği
 * @param {string} position - 'top' | 'bottom' | 'left' | 'right'
 * @param {number} delay - Gösterilme gecikmesi (ms)
 */
const Tooltip = ({
  children,
  content,
  position = 'top',
  delay = 300
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [timeoutId, setTimeoutId] = useState(null);
  
  const handleMouseEnter = () => {
    const id = setTimeout(() => {
      setIsVisible(true);
    }, delay);
    setTimeoutId(id);
  };
  
  const handleMouseLeave = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    setIsVisible(false);
  };
  
  if (!content) {
    return children;
  }
  
  return (
    <div
      className="tooltip-wrapper"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={handleMouseEnter}
      onBlur={handleMouseLeave}
    >
      {children}
      {isVisible && (
        <div className={`tooltip tooltip-${position} animate-fadeIn`} role="tooltip">
          {content}
          <div className={`tooltip-arrow tooltip-arrow-${position}`} />
        </div>
      )}
    </div>
  );
};

export default Tooltip;

