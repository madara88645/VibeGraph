import { useCallback, useRef, useState } from 'react';

import {
  ensureAiReady,
  fetchAiJson,
  getFriendlyAiErrorMessage,
} from '../utils/aiClient';

const MISSING_KEY_MESSAGE =
  'Open AI Settings and add your OpenRouter key to unlock explanations.';

export function useNodeInteraction({
  aiApiKey = '',
  selectedModel = '',
  aiReady = true,
  onRequireAiKey,
} = {}) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const explanationCacheRef = useRef(null);
  if (explanationCacheRef.current === null) {
    try {
      const saved = localStorage.getItem('vg_v1_explanationCache');
      explanationCacheRef.current = saved ? new Map(JSON.parse(saved)) : new Map();
    } catch {
      explanationCacheRef.current = new Map();
    }
  }

  const [codePanelOpen, setCodePanelOpen] = useState(true);
  const [codePanelNode, setCodePanelNode] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [learningPathOpen, setLearningPathOpen] = useState(false);

  const fetchExplanation = useCallback(
    async (node, type = 'technical', level = 'intermediate') => {
      const cacheKey = `${node.id}__${type}__${level}`;
      const cached = explanationCacheRef.current.get(cacheKey);
      if (cached) {
        setExplanation(cached);
        setLoading(false);
        return;
      }

      if (!ensureAiReady(aiReady, onRequireAiKey, MISSING_KEY_MESSAGE)) {
        setExplanation(MISSING_KEY_MESSAGE);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const filePath = node.data.file || node.data.original_data?.file;
        const payload = {
          file_path: filePath || null,
          node_id: node.id,
          type,
          level,
          model: selectedModel || null,
        };

        const data = await fetchAiJson('/api/explain', {
          apiKey: aiApiKey,
          body: payload,
        });
        const result = data.explanation ? data : 'No explanation returned.';
        explanationCacheRef.current.set(cacheKey, result);
        try {
          localStorage.setItem(
            'vg_v1_explanationCache',
            JSON.stringify([...explanationCacheRef.current.entries()])
          );
        } catch {
          // Ignore localStorage write errors.
        }
        setExplanation(result);
      } catch (error) {
        const message = getFriendlyAiErrorMessage(
          error,
          'Failed to reach Vibe Teacher.'
        );
        if (message.toLowerCase().includes('api key')) {
          onRequireAiKey?.(message);
        }
        setExplanation(message);
      } finally {
        setLoading(false);
      }
    },
    [aiApiKey, aiReady, onRequireAiKey, selectedModel]
  );

  const handleSelectNode = useCallback((node) => {
    setSelectedNode(node);
    setCodePanelNode(node);
  }, []);

  const onNodeClick = useCallback(
    async (event, node) => {
      handleSelectNode(node);
      setExplanation(null);
      setLoading(true);
      fetchExplanation(node, 'technical', 'intermediate');
    },
    [fetchExplanation, handleSelectNode]
  );

  const resetInteractionState = useCallback(() => {
    setSelectedNode(null);
    setExplanation(null);
    explanationCacheRef.current.clear();
    try {
      localStorage.removeItem('vg_v1_explanationCache');
    } catch {
      // Ignore localStorage remove errors.
    }
  }, []);

  return {
    selectedNode,
    setSelectedNode,
    explanation,
    setExplanation,
    loading,
    setLoading,
    codePanelOpen,
    setCodePanelOpen,
    codePanelNode,
    setCodePanelNode,
    chatOpen,
    setChatOpen,
    learningPathOpen,
    setLearningPathOpen,
    fetchExplanation,
    handleSelectNode,
    onNodeClick,
    resetInteractionState,
  };
}
