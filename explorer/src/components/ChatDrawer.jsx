import React, { useState, useCallback, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

import { consumeSseChunk } from '../utils/sse';

const ChatDrawer = ({ selectedNode, allNodes, isOpen, onToggle }) => {
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // Auto-scroll to bottom on new message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, loading]);

    // Focus input when drawer opens
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 200);
        }
    }, [isOpen]);

    // Reset messages when selected node identity changes
    const selectedNodeId = selectedNode?.id;
    useEffect(() => {
        if (selectedNodeId) {
            setMessages([]);
        }
    }, [selectedNodeId]);

    const sendMessage = useCallback(async () => {
        const text = inputText.trim();
        if (!text || loading) return;

        const userMsg = { role: 'user', content: text };
        const newMessages = [...messages, userMsg];
        setMessages(newMessages);
        setInputText('');
        setLoading(true);

        let projectContext = "No project loaded.";
        if (allNodes && allNodes.length > 0) {
            const types = allNodes.reduce((acc, n) => {
                const t = n.data?.type || 'unknown';
                acc[t] = (acc[t] || 0) + 1;
                return acc;
            }, {});
            const typeStr = Object.entries(types).map(([k, v]) => `${v} ${k}s`).join(', ');
            const fileNames = [...new Set(allNodes.map(n => n.data?.file).filter(Boolean))];
            
            // Limit to top 20 nodes to prevent context bloat, but show their names
            const coreNodes = allNodes
                .filter(n => n.data?.type === 'class' || n.data?.type === 'function')
                .slice(0, 20)
                .map(n => n.id)
                .join(', ');

            projectContext = `Project Overview: ${allNodes.length} total elements (${typeStr}) across ${fileNames.length} files.
Files included: ${fileNames.join(', ')}
Key functions/classes: ${coreNodes}${allNodes.length > 20 ? '...' : ''}`;
        }

        // Add placeholder assistant message for streaming
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
                // Fallback to non-streaming endpoint
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
                // Stream tokens from SSE
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
            console.error("Chat error:", err);
            setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                    role: 'assistant',
                    content: '\u26a0\ufe0f Could not reach the backend. Is serve.py running?',
                };
                return updated;
            });
        } finally {
            setLoading(false);
        }
    }, [allNodes, inputText, loading, messages, selectedNode]);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    if (!isOpen) {
        return (
            <button className="chat-fab" onClick={onToggle} title="Open Chat" aria-label="Open Chat">
                💬
            </button>
        );
    }

    return (
        <div className="chat-drawer">
            <div className="chat-drawer-header">
                <div className="chat-drawer-title">
                    <span>💬</span>
                    <span>Vibe Chat</span>
                </div>
                {selectedNode && (
                    <span className="chat-context-badge">
                        Asking about: <strong>{selectedNode.data?.label || selectedNode.id}</strong>
                    </span>
                )}
                <button className="chat-drawer-close" onClick={onToggle} aria-label="Close Chat">✕</button>
            </div>

            <div className="chat-messages">
                {messages.length === 0 && !loading && (
                    <div className="chat-empty">
                        {selectedNode
                            ? `Ask anything about "${selectedNode.data?.label || selectedNode.id}"…`
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
                    placeholder="Ask a question…"
                    aria-label="Chat input"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={1}
                />
                <span
                    className="chat-send-wrapper"
                    title={loading ? "Waiting for AI response..." : !inputText.trim() ? "Type a message to send" : "Send message"}
                >
                    <button
                        className="chat-send"
                        onClick={sendMessage}
                        disabled={loading || !inputText.trim()}
                        aria-label="Send message"
                    >
                        ↑
                    </button>
                </span>
            </div>
        </div>
    );
};

// PERFORMANCE OPTIMIZATION (Bolt):
// Wrap ChatDrawer in React.memo() to prevent parsing/rendering
// chat history Markdown on every tick during rapid simulation state changes.
export default React.memo(ChatDrawer);
