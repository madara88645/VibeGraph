import React, { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';

import {
  buildAiHeaders,
  ensureAiReady,
  fetchAiJson,
  getFriendlyAiErrorMessage,
} from '../utils/aiClient';
import { consumeSseChunk } from '../utils/sse';

const MISSING_KEY_MESSAGE =
  'Open AI Settings and add your OpenRouter key before starting a chat.';

const ChatDrawer = ({
  selectedNode,
  allNodes,
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

  const sendMessage = useCallback(async () => {
    const text = inputText.trim();
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

    const userMsg = { role: 'user', content: text };
    const nextMessages = [...messages, userMsg];
    setMessages([...nextMessages, { role: 'assistant', content: '' }]);
    setInputText('');
    setLoading(true);

    let projectContext = 'No project loaded.';
    if (allNodes && allNodes.length > 0) {
      const types = allNodes.reduce((acc, node) => {
        const type = node.data?.type || 'unknown';
        acc[type] = (acc[type] || 0) + 1;
        return acc;
      }, {});
      const typeStr = Object.entries(types)
        .map(([key, value]) => `${value} ${key}s`)
        .join(', ');
      const fileNames = [...new Set(allNodes.map((node) => node.data?.file).filter(Boolean))];

      // PERFORMANCE OPTIMIZATION (Bolt): Use a for-loop with early exit instead of .filter().slice(0, 20)
      // This drops the execution time from an unconditional O(N) down to a best-case O(K).
      const coreNodeIds = [];
      for (let i = 0; i < allNodes.length; i++) {
        if (coreNodeIds.length >= 20) break;
        const node = allNodes[i];
        if (node.data?.type === 'class' || node.data?.type === 'function') {
          coreNodeIds.push(node.id);
        }
      }
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

  if (!isOpen) {
    return (
      <button className="chat-fab" onClick={onToggle} title="Open Chat" aria-label="Open Chat">
        <span aria-hidden="true">{'Chat'}</span>
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
        {selectedNode ? (
          <span className="chat-context-badge">
            Asking about: <strong>{selectedNode.data?.label || selectedNode.id}</strong>
          </span>
        ) : null}
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
              `Ask anything about "${selectedNode.data?.label || selectedNode.id}"...`
            ) : (
              'Ask a general question about the uploaded project!'
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
        <textarea
          ref={inputRef}
          className="chat-input"
          placeholder="Ask a question..."
          aria-label="Chat input"
          value={inputText}
          onChange={(event) => setInputText(event.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
        />
        <span
          style={{ display: 'inline-flex' }}
          className="chat-send-wrapper"
          title={
            loading
              ? 'Waiting for AI response...'
              : !inputText.trim()
                ? 'Type a message to send'
                : 'Send message'
          }
        >
          <button
            className="chat-send"
            onClick={sendMessage}
            disabled={loading || !inputText.trim()}
            aria-label="Send message"
          >
            <span aria-hidden="true">{'^'}</span>
          </button>
        </span>
      </div>
    </div>
  );
};

export default React.memo(ChatDrawer);
