import { useEffect, useRef } from 'react';

/**
 * Touch gesture (swipe) desteği için custom hook
 * @param {Function} onSwipeLeft - Sola kaydırma callback
 * @param {Function} onSwipeRight - Sağa kaydırma callback
 * @param {number} threshold - Minimum kaydırma mesafesi (px)
 */
export const useSwipe = (onSwipeLeft, onSwipeRight, threshold = 50) => {
  const touchStartX = useRef(0);
  const touchEndX = useRef(0);
  const elementRef = useRef(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const handleTouchStart = (e) => {
      touchStartX.current = e.touches[0].clientX;
    };

    const handleTouchMove = (e) => {
      touchEndX.current = e.touches[0].clientX;
    };

    const handleTouchEnd = () => {
      const swipeDistance = touchStartX.current - touchEndX.current;

      if (Math.abs(swipeDistance) > threshold) {
        if (swipeDistance > 0 && onSwipeLeft) {
          // Sola kaydırma
          onSwipeLeft();
        } else if (swipeDistance < 0 && onSwipeRight) {
          // Sağa kaydırma
          onSwipeRight();
        }
      }

      // Reset
      touchStartX.current = 0;
      touchEndX.current = 0;
    };

    element.addEventListener('touchstart', handleTouchStart, { passive: true });
    element.addEventListener('touchmove', handleTouchMove, { passive: true });
    element.addEventListener('touchend', handleTouchEnd);

    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }, [onSwipeLeft, onSwipeRight, threshold]);

  return elementRef;
};

