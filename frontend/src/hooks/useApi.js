/**
 * ===================================
 * منصة ديواني - Custom API Hooks
 * Modern React hooks for data fetching
 * ===================================
 */

import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * useApi - Generic hook for API calls with loading, error, and caching
 */
export function useApi(apiFunction, options = {}) {
  const {
    immediate = false,
    initialData = null,
    onSuccess,
    onError,
    cacheKey,
    cacheDuration = 5 * 60 * 1000, // 5 minutes default
  } = options;

  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const mountedRef = useRef(true);
  const cacheRef = useRef(new Map());

  // Check cache
  const getCached = useCallback((key) => {
    if (!key) return null;
    const cached = cacheRef.current.get(key);
    if (cached && Date.now() - cached.timestamp < cacheDuration) {
      return cached.data;
    }
    return null;
  }, [cacheDuration]);

  // Set cache
  const setCache = useCallback((key, value) => {
    if (!key) return;
    cacheRef.current.set(key, {
      data: value,
      timestamp: Date.now(),
    });
  }, []);

  // Execute API call
  const execute = useCallback(async (...args) => {
    // Check cache first
    const cached = getCached(cacheKey);
    if (cached) {
      setData(cached);
      return cached;
    }

    try {
      setLoading(true);
      setError(null);

      const result = await apiFunction(...args);

      if (mountedRef.current) {
        setData(result);
        setCache(cacheKey, result);
        onSuccess?.(result);
      }

      return result;
    } catch (err) {
      if (mountedRef.current) {
        setError(err);
        onError?.(err);
      }
      throw err;
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [apiFunction, cacheKey, getCached, setCache, onSuccess, onError]);

  // Refetch without cache
  const refetch = useCallback(async (...args) => {
    if (cacheKey) {
      cacheRef.current.delete(cacheKey);
    }
    return execute(...args);
  }, [execute, cacheKey]);

  // Reset state
  const reset = useCallback(() => {
    setData(initialData);
    setError(null);
    setLoading(false);
  }, [initialData]);

  // Immediate execution
  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate]); // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    refetch,
    reset,
    setData,
  };
}

/**
 * usePagination - Hook for paginated data
 */
export function usePagination(apiFunction, options = {}) {
  const { pageSize = 10, initialPage = 1 } = options;

  const [page, setPage] = useState(initialPage);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPage = useCallback(async (pageNum, filters = {}) => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiFunction({
        page: pageNum,
        page_size: pageSize,
        ...filters,
      });

      setItems(response.items || []);
      setTotalPages(response.pages || 1);
      setTotal(response.total || 0);
      setPage(pageNum);

      return response;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiFunction, pageSize]);

  const nextPage = useCallback(() => {
    if (page < totalPages) {
      fetchPage(page + 1);
    }
  }, [page, totalPages, fetchPage]);

  const prevPage = useCallback(() => {
    if (page > 1) {
      fetchPage(page - 1);
    }
  }, [page, fetchPage]);

  const goToPage = useCallback((pageNum) => {
    if (pageNum >= 1 && pageNum <= totalPages) {
      fetchPage(pageNum);
    }
  }, [totalPages, fetchPage]);

  return {
    items,
    loading,
    error,
    page,
    totalPages,
    total,
    pageSize,
    hasNext: page < totalPages,
    hasPrev: page > 1,
    fetchPage,
    nextPage,
    prevPage,
    goToPage,
    setItems,
  };
}

/**
 * useDebounce - Hook for debounced values
 */
export function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * useLocalStorage - Hook for persistent state
 */
export function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(error);
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(error);
    }
  }, [key, storedValue]);

  const removeValue = useCallback(() => {
    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.error(error);
    }
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue];
}

/**
 * useOnClickOutside - Hook for detecting clicks outside element
 */
export function useOnClickOutside(ref, handler) {
  useEffect(() => {
    const listener = (event) => {
      if (!ref.current || ref.current.contains(event.target)) {
        return;
      }
      handler(event);
    };

    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);

    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref, handler]);
}

/**
 * useIntersectionObserver - Hook for lazy loading / infinite scroll
 */
export function useIntersectionObserver(options = {}) {
  const { threshold = 0, root = null, rootMargin = '0px' } = options;
  const [entry, setEntry] = useState(null);
  const [node, setNode] = useState(null);

  const observer = useRef(null);

  useEffect(() => {
    if (observer.current) {
      observer.current.disconnect();
    }

    observer.current = new IntersectionObserver(
      ([entry]) => setEntry(entry),
      { threshold, root, rootMargin }
    );

    if (node) {
      observer.current.observe(node);
    }

    return () => {
      if (observer.current) {
        observer.current.disconnect();
      }
    };
  }, [node, threshold, root, rootMargin]);

  return [setNode, entry];
}

/**
 * useMediaQuery - Hook for responsive design
 */
export function useMediaQuery(query) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }

    const listener = () => setMatches(media.matches);
    media.addEventListener('change', listener);

    return () => media.removeEventListener('change', listener);
  }, [matches, query]);

  return matches;
}

/**
 * useWindowSize - Hook for window dimensions
 */
export function useWindowSize() {
  const [size, setSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
  });

  useEffect(() => {
    const handleResize = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return size;
}

export default {
  useApi,
  usePagination,
  useDebounce,
  useLocalStorage,
  useOnClickOutside,
  useIntersectionObserver,
  useMediaQuery,
  useWindowSize,
};
