import React, { useState, useCallback, useEffect, useRef } from 'react';

// 批量更新状态的Hook
export function useBatchedState<T>(initialState: T) {
  const [state, setState] = useState<T>(initialState);
  const updateQueueRef = useRef<((prev: T) => T)[]>([]);
  const isProcessingRef = useRef(false);

  const batchUpdate = useCallback((updater: (prev: T) => T) => {
    updateQueueRef.current.push(updater);

    if (!isProcessingRef.current) {
      isProcessingRef.current = true;

      // 使用requestAnimationFrame确保批量更新在一次渲染周期内完成
      requestAnimationFrame(() => {
        setState(prevState => {
          let newState = prevState;
          updateQueueRef.current.forEach(update => {
            newState = update(newState);
          });
          updateQueueRef.current = [];
          isProcessingRef.current = false;
          return newState;
        });
      });
    }
  }, []);

  return [state, batchUpdate] as const;
}

// 持久化状态的Hook
export function usePersistedState<T>(key: string, initialState: T) {
  const [state, setState] = useState<T>(() => {
    try {
      const savedState = localStorage.getItem(key);
      return savedState ? JSON.parse(savedState) : initialState;
    } catch (error) {
      console.error('Error loading persisted state:', error);
      return initialState;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(state));
    } catch (error) {
      console.error('Error saving persisted state:', error);
    }
  }, [key, state]);

  return [state, setState] as const;
}

// 防抖状态更新的Hook
export function useDebouncedState<T>(initialState: T, delay: number) {
  const [state, setState] = useState<T>(initialState);
  const [debouncedState, setDebouncedState] = useState<T>(initialState);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      setDebouncedState(state);
    }, delay);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [state, delay]);

  return [state, setState, debouncedState] as const;
}

// 优化的Context更新Hook
export function useContextUpdater<T>(context: React.Context<T | undefined>) {
  const contextValue = React.useContext(context);

  if (contextValue === undefined) {
    throw new Error('useContextUpdater must be used within a provider');
  }

  return contextValue;
}
