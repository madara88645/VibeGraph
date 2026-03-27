import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useReactFlow } from 'reactflow';

const SearchBar = ({ allNodes, onSelectNode, onSelectFile }) => {
    const [query, setQuery] = useState('');
    const [isOpen, setIsOpen] = useState(false);
    const [highlightIdx, setHighlightIdx] = useState(0);
    const inputRef = useRef(null);
    const containerRef = useRef(null);
    const { setCenter } = useReactFlow();

    // Keyboard shortcut: Ctrl+K or /
    useEffect(() => {
        const handler = (e) => {
            if ((e.ctrlKey && e.key === 'k') || (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName))) {
                e.preventDefault();
                inputRef.current?.focus();
                setIsOpen(true);
            }
            if (e.key === 'Escape') {
                setIsOpen(false);
                setQuery('');
                inputRef.current?.blur();
            }
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, []);

    // Click outside to close
    useEffect(() => {
        const handler = (e) => {
            if (containerRef.current && !containerRef.current.contains(e.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    // Fuzzy match: simple case-insensitive substring match on label + file
    const results = React.useMemo(() => {
        if (!query.trim()) return [];
        const q = query.toLowerCase();
        return allNodes
            .filter((n) => {
                const label = (n.data?.label || '').toLowerCase();
                const file = (n.data?.file || '').toLowerCase();
                return label.includes(q) || file.includes(q);
            })
            .slice(0, 8);
    }, [query, allNodes]);

    const handleSelect = useCallback((node) => {
        if (node.data?.file) onSelectFile(node.data.file);
        onSelectNode(node);
        // Zoom to node
        if (node.position) {
            setCenter(node.position.x + 86, node.position.y + 18, { zoom: 1.5, duration: 600 });
        }
        setIsOpen(false);
        setQuery('');
    }, [onSelectFile, onSelectNode, setCenter]);

    const handleKeyDown = (e) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setHighlightIdx((i) => Math.min(i + 1, results.length - 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setHighlightIdx((i) => Math.max(i - 1, 0));
        } else if (e.key === 'Enter' && results[highlightIdx]) {
            handleSelect(results[highlightIdx]);
        }
    };

    const typeIcon = (node) => {
        if (node.data?.entry_point) return '🚀';
        if (node.data?.type === 'class') return '🏗️';
        return '⚡';
    };

    return (
        <div className="search-bar" ref={containerRef}>
            <div className="search-input-wrapper">
                <span className="search-icon">🔍</span>
                <input
                    ref={inputRef}
                    type="text"
                    className="search-input"
                    placeholder="Search nodes... (Ctrl+K)"
                    aria-label="Search nodes"
                    value={query}
                    onChange={(e) => { setQuery(e.target.value); setIsOpen(true); setHighlightIdx(0); }}
                    onFocus={() => setIsOpen(true)}
                    onKeyDown={handleKeyDown}
                />
                {query && (
                    <button className="search-clear" onClick={() => { setQuery(''); setIsOpen(false); }} title="Clear Search" aria-label="Clear Search">✕</button>
                )}
            </div>

            {isOpen && results.length > 0 && (
                <div className="search-results">
                    {results.map((node, idx) => (
                        <button
                            key={node.id}
                            className={`search-result-item ${idx === highlightIdx ? 'highlighted' : ''}`}
                            onClick={() => handleSelect(node)}
                            onMouseEnter={() => setHighlightIdx(idx)}
                        >
                            <span className="search-result-icon">{typeIcon(node)}</span>
                            <div className="search-result-text">
                                <span className="search-result-label">{node.data?.label || node.id}</span>
                                {node.data?.file && (
                                    <span className="search-result-file">
                                        {node.data.file.split(/[/\\]/).pop()}
                                    </span>
                                )}
                            </div>
                        </button>
                    ))}
                </div>
            )}

            {isOpen && query.trim() && results.length === 0 && (
                <div className="search-results">
                    <div className="search-no-results">No matching nodes found</div>
                </div>
            )}
        </div>
    );
};

// PERFORMANCE OPTIMIZATION (Bolt):
// Wrap SearchBar in React.memo() to prevent O(N) fuzzy search evaluations
// or re-renders during rapid simulation state changes in the App.
export default React.memo(SearchBar);
