import React, { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';

import { consumeSseChunk } from '../utils/sse';

const ChatDrawer = ({ selectedNode, allNodes, isOpen, onToggle }) => {
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

  const sendMessage = useCallback(async () => {
    const text = inputText.trim();
    if (!text || loading) return;

    const userMsg = { role: 'user', content: text };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
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

      const coreNodes = allNodes
        .filter((node) => node.data?.type === 'class' || node.data?.type === 'function')
        .slice(0, 20)
        .map((node) => node.id)
        .join(', ');

      projectContext = `Project Overview: ${allNodes.length} total elements (${typeStr}) across ${fileNames.length} files.
Files included: ${fileNames.join(', ')}
Key functions/classes: ${coreNodes}${allNodes.length > 20 ? '...' : ''}`;
    }

    setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

    try {
      const requestBody = JSON.stringify({
        node_id: selectedNode?.id || null,
        file_path: selectedNode?.data?.file || null,
        project_context: projectContext,
        question: text,
        history: newMessages.slice(-10),
      });

      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: requestBody,
      });

      if (!response.ok || !response.body) {
        const fallbackResp = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: requestBody,
        });
        const data = await fallbackResp.json();
        const aiContent = data.answer || data.response || data.message || 'No response.';
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: 'assistant', content: aiContent };
          return updated;
        });
      } else {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let streamDone = false;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const parsed = consumeSseChunk(buffer, chunk);
          buffer = parsed.buffer;

          for (const eventData of parsed.events) {
            if (eventData === '[DONE]') {
              streamDone = true;
              break;
            }

            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              updated[updated.length - 1] = {
                ...last,
                content: last.content + eventData,
              };
              return updated;
            });
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

            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              updated[updated.length - 1] = {
                ...last,
                content: last.content + eventData,
              };
              return updated;
            });
          }
        }
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: 'assistant',
          content: '\u26A0\uFE0F Could not reach the backend. Is serve.py running?',
        };
        return updated;
      });
    } finally {
      setLoading(false);
      if (selectedNode?.id) {
        setMessages((prev) => {
          try {
            localStorage.setItem(`vg_v1_chat_${selectedNode.id}`, JSON.stringify(prev));
          } catch {}
          return prev;
        });
      }
    }
  }, [allNodes, inputText, loading, messages, selectedNode]);

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  if (!isOpen) {
    return (
      <button className="chat-fab" onClick={onToggle} title="Open Chat" aria-label="Open Chat">
        {'\uD83D\uDCAC'}
      </button>
    );
  }

  return (
    <div className="chat-drawer">
      <div className="chat-drawer-header">
        <div className="chat-drawer-title">
          <span>{'\uD83D\uDCAC'}</span>
          <span>Vibe Chat</span>
        </div>
        {selectedNode && (
          <span className="chat-context-badge">
            Asking about: <strong>{selectedNode.data?.label || selectedNode.id}</strong>
          </span>
        )}
        <button className="chat-drawer-close" onClick={onToggle} aria-label="Close Chat">
          {'\u2715'}
        </button>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && !loading && (
          <div className="chat-empty">
            {selectedNode
              ? `Ask anything about "${selectedNode.data?.label || selectedNode.id}"...`
              : 'Ask a general question about the uploaded project!'}
          </div>
        )}

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

        {loading && messages.length > 0 && messages[messages.length - 1]?.content === '' && (
          <div className="chat-message chat-message-assistant">
            <div className="chat-bubble chat-typing">
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
            </div>
          </div>
        )}

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
            {'\u2191'}
          </button>
        </span>
      </div>
    </div>
  );
};

export default React.memo(ChatDrawer);
