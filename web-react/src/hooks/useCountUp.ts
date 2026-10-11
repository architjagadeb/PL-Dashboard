import { useEffect, useState } from 'react';

interface UseCountUpOptions {
  duration?: number;
  decimals?: number;
  enabled?: boolean;
}

export function useCountUp(
  targetValue: number,
  { duration = 750, decimals = 0, enabled = true }: UseCountUpOptions = {}
): string {
  const [displayValue, setDisplayValue] = useState<number>(0);

  useEffect(() => {
    if (!enabled || isNaN(targetValue) || targetValue <= 0) {
      setDisplayValue(targetValue);
      return;
    }

    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      setDisplayValue(targetValue);
      return;
    }

    let animationFrameId: number;
    const startTime = performance.now();

    function update(currentTime: number) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Cubic ease-out: 1 - (1 - progress)^3
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const currentVal = targetValue * easeOut;

      setDisplayValue(currentVal);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(update);
      } else {
        setDisplayValue(targetValue);
      }
    }

    animationFrameId = requestAnimationFrame(update);

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [targetValue, duration, enabled]);

  if (decimals === 0) {
    return Math.round(displayValue).toLocaleString();
  }
  return displayValue.toFixed(decimals);
}
