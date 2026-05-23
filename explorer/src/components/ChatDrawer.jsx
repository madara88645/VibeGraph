import React, { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';

import {
  buildAiHeaders,
  ensureAiReady,
  fetchAiJson,
  getFriendlyAiErrorMessage,
} from '../utils/aiClient';
import { buildNodeGroundingContext } from '../utils/graphContext';
import { consumeSseChunk } from '../utils/sse';

const MISSING_KEY_MESSAGE =
  'Open AI Settings and add your OpenRouter key before starting a chat.';

const NO_NODE_MESSAGE =
  'Pick a function or class on the graph first so answers use real code from your project.';

const NO_NODE_PLACEHOLDER = 'Select a node on the graph to ask…';

const ChatDrawer = ({
  selectedNode,
  allNodes,
  allEdges,
  isOpen,
  onToggle,
  apiKey,
  selectedModel,
  aiReady,
  onOpenAiSettings,
}) => {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 200);
    }
  }, [isOpen]);

  useEffect(() => {
    if (!selectedNode?.id) {
      setMessages([]);
      return;
    }

    try {
      const saved = localStorage.getItem(`vg_v1_chat_${selectedNode.id}`);
      setMessages(saved ? JSON.parse(saved) : []);
    } catch {
      setMessages([]);
    }
  }, [selectedNode?.id]);

  const persistMessages = useCallback(
    (nextMessages) => {
      if (!selectedNode?.id) {
        return;
      }
      try {
        localStorage.setItem(`vg_v1_chat_${selectedNode.id}`, JSON.stringify(nextMessages));
      } catch {
        // Ignore storage write issues.
      }
    },
    [selectedNode?.id]
  );

  const sendMessage = useCallback(async (overrideText) => {
    const rawText =
      typeof overrideText === 'string' && overrideText.trim()
        ? overrideText
        : inputText;
    const text = rawText.trim();
    if (!text || loading) {
      return;
    }

    if (!ensureAiReady(aiReady, onOpenAiSettings, MISSING_KEY_MESSAGE)) {
      const promptMessages = [
        ...messages,
        { role: 'user', content: text },
        { role: 'assistant', content: MISSING_KEY_MESSAGE },
      ];
      setMessages(promptMessages);
      persistMessages(promptMessages);
      setInputText('');
      return;
    }

    if (!selectedNode?.id) {
      const promptMessages = [
        ...messages,
        { role: 'user', content: text },
        { role: 'assistant', content: NO_NODE_MESSAGE },
      ];
      setMessages(promptMessages);
      setInputText('');
      return;
    }

    const userMsg = { role: 'user', content: text };
    const nextMessages = [...messages, userMsg];
    setMessages([...nextMessages, { role: 'assistant', content: '' }]);
    setInputText('');
    setLoading(true);

    let projectContext = 'No project loaded.';
    if (allNodes && allNodes.length > 0) {
      // PERFORMANCE OPTIMIZATION (Bolt): Replaced multiple O(N) array method chains
      // (reduce, map, filter) with a single unified O(N) for-loop to accumulate types,
      // filesSet, and coreNodeIds. This significantly reduces CPU overhead and intermediate object allocations.
      const types = {};
      const filesSet = new Set();
      const coreNodeIds = [];

      for (let i = 0; i < allNodes.length; i++) {
        const node = allNodes[i];

        // Count types
        const type = node.data?.type || 'unknown';
        types[type] = (types[type] || 0) + 1;

        // Collect files
        if (node.data?.file) {
          filesSet.add(node.data.file);
        }

        // Collect core nodes (max 20)
        if (coreNodeIds.length < 20 && (type === 'class' || type === 'function')) {
          coreNodeIds.push(node.id);
        }
      }

      const typeStr = Object.entries(types)
        .map(([key, value]) => `${value} ${key}s`)
        .join(', ');
      const fileNames = [...filesSet];

      const coreNodes = coreNodeIds.join(', ');

      projectContext = `Project Overview: ${allNodes.length} total elements (${typeStr}) across ${fileNames.length} files.
Files included: ${fileNames.join(', ')}
Key functions/classes: ${coreNodes}${allNodes.length > 20 ? '...' : ''}`;
    }

    const requestBody = {
      node_id: selectedNode?.id || null,
      file_path: selectedNode?.data?.file || null,
      project_context: projectContext,
      question: text,
      history: nextMessages.slice(-10),
      model: selectedModel || null,
      ...buildNodeGroundingContext({
        nodeId: selectedNode?.id || null,
        allNodes,
        allEdges,
      }),
    };

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: buildAiHeaders(apiKey),
        body: JSON.stringify(requestBody),
      });

      if (!response.ok || !response.body) {
        const fallbackData = await fetchAiJson('/api/chat', {
          apiKey,
          body: requestBody,
        });
        const aiContent =
          fallbackData.answer ||
          fallbackData.response ||
          fallbackData.message ||
          'No response.';
        const updatedMessages = [...nextMessages, { role: 'assistant', content: aiContent }];
        setMessages(updatedMessages);
        persistMessages(updatedMessages);
      } else {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let streamDone = false;
        let assistantContent = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            break;
          }

          const chunk = decoder.decode(value, { stream: true });
          const parsed = consumeSseChunk(buffer, chunk);
          buffer = parsed.buffer;

          for (const eventData of parsed.events) {
            if (eventData === '[DONE]') {
              streamDone = true;
              break;
            }

            assistantContent += eventData;
            setMessages([...nextMessages, { role: 'assistant', content: assistantContent }]);
          }

          if (streamDone) {
            break;
          }
        }

        if (!streamDone && buffer) {
          const parsed = consumeSseChunk(buffer, '\n\n');
          for (const eventData of parsed.events) {
            if (eventData === '[DONE]') {
              break;
            }
            assistantContent += eventData;
          }
          setMessages([...nextMessages, { role: 'assistant', content: assistantContent }]);
        }

        persistMessages([...nextMessages, { role: 'assistant', content: assistantContent }]);
      }
    } catch (error) {
      const errorMessage = getFriendlyAiErrorMessage(
        error,
        'Could not reach the backend. Is serve.py running?'
      );
      if (errorMessage.toLowerCase().includes('api key')) {
        onOpenAiSettings?.(errorMessage);
      }
      const updatedMessages = [
        ...nextMessages,
        {
          role: 'assistant',
          content: errorMessage,
        },
      ];
      setMessages(updatedMessages);
      persistMessages(updatedMessages);
    } finally {
      setLoading(false);
    }
  }, [
    aiReady,
    allNodes,
    allEdges,
    apiKey,
    inputText,
    loading,
    messages,
    onOpenAiSettings,
    persistMessages,
    selectedModel,
    selectedNode,
  ]);

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const hasSelectedNode = Boolean(selectedNode?.id);
  const canSend = hasSelectedNode && !loading && Boolean(inputText.trim());

  const sendDisabledReason = loading
    ? 'Waiting for AI response...'
    : !hasSelectedNode
      ? 'Select a graph node to send'
      : !inputText.trim()
        ? 'Type a message to send'
        : 'Send message';

  if (!isOpen) {
    return (
      <button className="chat-fab" onClick={onToggle} title="Open Chat" aria-label="Open Chat">
        <svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'white' }}>
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </button>
    );
  }

  return (
    <div className="chat-drawer">
      <div className="chat-drawer-header">
        <div className="chat-drawer-title">
          <span aria-hidden="true">{'Chat'}</span>
          <span>Vibe Chat</span>
        </div>
        {hasSelectedNode ? (
          <span className="chat-context-badge">
            Asking about: <strong>{selectedNode.data?.label || selectedNode.id}</strong>
          </span>
        ) : (
          <span className="chat-context-badge chat-no-node-badge">No node selected</span>
        )}
        <button className="chat-drawer-close" onClick={onToggle} title="Close Chat" aria-label="Close Chat">
          <span aria-hidden="true">x</span>
        </button>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && !loading ? (
          <div className="chat-empty">
            {!aiReady ? (
              <>
                <p>Open AI Settings and add your OpenRouter key to start chatting.</p>
                <button
                  type="button"
                  className="header-action-btn"
                  onClick={() => onOpenAiSettings?.(MISSING_KEY_MESSAGE)}
                >
                  Open AI Settings
                </button>
              </>
            ) : selectedNode ? (
              <>
                <p className="chat-empty-lead">
                  Ask anything about "{selectedNode.data?.label || selectedNode.id}"...
                </p>
                <div className="chat-suggestions" aria-label="Suggested questions">
                  {[
                    'Explain what this does in plain English',
                    'How is this used elsewhere in the project?',
                    'What could go wrong here?',
                  ].map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      className="chat-suggestion"
                      onClick={() => sendMessage(prompt)}
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <>
                <p className="chat-empty-lead">
                  Select a function or class on the graph to chat about real code from your
                  project.
                </p>
                <ul className="chat-empty-tips" aria-label="How to select a node">
                  <li>Click any node on the graph</li>
                  <li>Or press Ctrl+K to search and jump to a node</li>
                  <li>Use Learn in the header for a guided study order</li>
                </ul>
              </>
            )}
          </div>
        ) : null}

        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-message chat-message-${msg.role}`}>
            <div className="chat-bubble">
              {msg.role === 'assistant' ? (
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              ) : (
                <span>{msg.content}</span>
              )}
            </div>
          </div>
        ))}

        {loading && messages.length > 0 && messages[messages.length - 1]?.content === '' ? (
          <div className="chat-message chat-message-assistant">
            <div className="chat-bubble chat-typing">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        ) : null}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <label htmlFor="chat-input" style={{ position: 'absolute', width: '1px', height: '1px', padding: '0', margin: '-1px', overflow: 'hidden', clip: 'rect(0, 0, 0, 0)', whiteSpace: 'nowrap', border: '0' }}>
          Chat input
        </label>
        <textarea
          id="chat-input"
          ref={inputRef}
          className="chat-input"
          placeholder={hasSelectedNode ? 'Ask a question...' : NO_NODE_PLACEHOLDER}
          aria-label="Chat input"
          value={inputText}
          onChange={(event) => setInputText(event.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
        />
        <span
          style={{ display: 'inline-flex' }}
          className="chat-send-wrapper"
          title={sendDisabledReason}
        >
          <button
            className="chat-send"
            onClick={sendMessage}
            disabled={!canSend}
            aria-label={sendDisabledReason}
          >
            <span aria-hidden="true">
              {loading ? (
                <span className="vibe-spinner" style={{ width: '16px', height: '16px', borderTopColor: 'var(--bg-panel)' }} />
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                </svg>
              )}
            </span>
          </button>
        </span>
      </div>
    </div>
  );
};

export default React.memo(ChatDrawer);
