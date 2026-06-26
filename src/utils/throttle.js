/**
 * Throttle execution of a function to run at most once per interval
 */
export function throttle(func, delay) {
  let lastCall = 0;
  let timeoutId = null;

  return function throttled(...args) {
    const now = Date.now();
    const timeSinceLastCall = now - lastCall;

    const execute = () => {
      lastCall = Date.now();
      timeoutId = null;
      func.apply(this, args);
    };

    if (timeSinceLastCall >= delay) {
      execute();
    } else if (!timeoutId) {
      timeoutId = setTimeout(execute, delay - timeSinceLastCall);
    }
  };
}

/**
 * Debounce execution of a function until after delay ms have elapsed
 */
export function debounce(func, delay) {
  let timeoutId = null;

  return function debounced(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
      func.apply(this, args);
      timeoutId = null;
    }, delay);
  };
}

/**
 * Request animation frame wrapper for smooth animations
 */
export function rafThrottle(func) {
  let rafId = null;
  let pendingArgs = null;

  return function rafThrottled(...args) {
    pendingArgs = args;

    if (!rafId) {
      rafId = requestAnimationFrame(() => {
        func.apply(this, pendingArgs);
        rafId = null;
        pendingArgs = null;
      });
    }
  };
}
