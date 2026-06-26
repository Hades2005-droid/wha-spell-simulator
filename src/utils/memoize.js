/**
 * Simple memoization for single-argument functions
 */
export function memoize(func, options = {}) {
  const cache = new Map();
  const maxSize = options.maxSize || 100;

  return function memoized(arg) {
    if (cache.has(arg)) {
      return cache.get(arg);
    }

    const result = func.call(this, arg);

    if (cache.size >= maxSize) {
      // Remove oldest entry when cache is full
      const oldestKey = cache.keys().next().value;
      cache.delete(oldestKey);
    }

    cache.set(arg, result);
    return result;
  };
}

/**
 * Memoization for functions with multiple arguments using JSON key
 */
export function memoizeDeep(func, options = {}) {
  const cache = new Map();
  const maxSize = options.maxSize || 50;

  return function memoized(...args) {
    const key = JSON.stringify(args);

    if (cache.has(key)) {
      return cache.get(key);
    }

    const result = func.apply(this, args);

    if (cache.size >= maxSize) {
      const oldestKey = cache.keys().next().value;
      cache.delete(oldestKey);
    }

    cache.set(key, result);
    return result;
  };
}

/**
 * Memoization with time-based expiration
 */
export function memoizeWithExpiry(func, delay, options = {}) {
  const cache = new Map();
  const timestamps = new Map();
  const maxSize = options.maxSize || 50;

  return function memoized(arg) {
    const now = Date.now();

    if (cache.has(arg)) {
      const timestamp = timestamps.get(arg);
      if (now - timestamp < delay) {
        return cache.get(arg);
      }
      cache.delete(arg);
      timestamps.delete(arg);
    }

    const result = func.call(this, arg);

    if (cache.size >= maxSize) {
      const oldestKey = cache.keys().next().value;
      cache.delete(oldestKey);
      timestamps.delete(oldestKey);
    }

    cache.set(arg, result);
    timestamps.set(arg, now);
    return result;
  };
}

/**
 * Clear all caches - useful for testing
 */
export function clearMemoCache(memoizedFunc) {
  if (memoizedFunc._cache) {
    memoizedFunc._cache.clear();
  }
}
