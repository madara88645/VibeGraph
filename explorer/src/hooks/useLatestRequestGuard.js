import { useCallback, useRef } from 'react';

/**
 * Monotonic request ids for async UI work where only the latest result may apply.
 */
export function useLatestRequestGuard() {
  const latestRequestIdRef = useRef(0);

  const beginRequest = useCallback(() => {
    latestRequestIdRef.current += 1;
    return latestRequestIdRef.current;
  }, []);

  const isLatestRequest = useCallback(
    (requestId) => latestRequestIdRef.current === requestId,
    []
  );

  const invalidateRequests = useCallback(() => {
    latestRequestIdRef.current += 1;
  }, []);

  return { beginRequest, isLatestRequest, invalidateRequests };
}
