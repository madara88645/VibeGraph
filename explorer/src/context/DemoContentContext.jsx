import { createContext, useCallback, useContext, useMemo, useState } from 'react';

const DemoContentContext = createContext(null);

export function DemoContentProvider({ children }) {
  const [content, setContent] = useState(null);

  const setDemoContent = useCallback((next) => {
    setContent(next && typeof next === 'object' ? next : null);
  }, []);
  const clearDemoContent = useCallback(() => setContent(null), []);

  const getBakedExplanation = useCallback(
    (nodeId, level) => {
      const entry = content?.explanations?.[nodeId];
      const detail = entry?.levels?.[level];
      if (!entry || !detail) {
        return null;
      }
      return { node_id: nodeId, explanation: detail, snippet: entry.snippet ?? '' };
    },
    [content]
  );

  const getCannedChats = useCallback(
    (nodeId) => (content?.chat ?? []).filter((c) => c.nodeId === nodeId),
    [content]
  );

  const value = useMemo(
    () => ({
      isDemo: Boolean(content),
      setDemoContent,
      clearDemoContent,
      getBakedExplanation,
      getCannedChats,
    }),
    [content, setDemoContent, clearDemoContent, getBakedExplanation, getCannedChats]
  );

  return <DemoContentContext.Provider value={value}>{children}</DemoContentContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useDemoContent() {
  const ctx = useContext(DemoContentContext);
  if (!ctx) {
    // Safe no-op shape so consumers work without a provider (e.g. isolated tests).
    return {
      isDemo: false,
      setDemoContent: () => {},
      clearDemoContent: () => {},
      getBakedExplanation: () => null,
      getCannedChats: () => [],
    };
  }
  return ctx;
}
