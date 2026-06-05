import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useReactFlow } from 'reactflow';

import { getShortName } from '../utils/stringUtils';

// WeakMap to cache computed search strings without mutating the original node objects
const searchCache = new WeakMap();

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
        const matches = [];
        // PERFORMANCE OPTIMIZATION (Bolt): Use a for-loop with early exit instead of .filter().slice(0, 8)
        // This avoids O(N) string processing across potentially thousands of nodes once we have our 8 results.
        for (let i = 0; i < allNodes.length; i++) {
            if (matches.length >= 8) break;
            const n = allNodes[i];

            // PERFORMANCE OPTIMIZATION (Bolt): Lazily precompute and cache the normalized
            // search string in a WeakMap to drastically reduce garbage collection
            // overhead and execution time during high-frequency UI search filters
            // without mutating the immutable node props.
            let searchStr = searchCache.get(n);
            if (searchStr === undefined) {
                const label = (n.data?.label || '').toLowerCase();
                const file = (n.data?.file || '').toLowerCase();
                searchStr = label + '|' + file;
                searchCache.set(n, searchStr);
            }

            if (searchStr.includes(q)) {
                matches.push(n);
            }
        }
        return matches;
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

    const listboxId = "search-results-listbox";

    return (
        <div className="search-bar" ref={containerRef}>
            <div className="search-input-wrapper">
                <label htmlFor="search-input" style={{ position: 'absolute', width: '1px', height: '1px', padding: '0', margin: '-1px', overflow: 'hidden', clip: 'rect(0, 0, 0, 0)', whiteSpace: 'nowrap', border: '0' }}>
                    Search nodes (Ctrl+K)
                </label>
                <span className="search-icon" aria-hidden="true">🔍</span>
                <input
                    id="search-input"
                    ref={inputRef}
                    type="text"
                    role="combobox"
                    aria-expanded={isOpen}
                    aria-controls={isOpen ? listboxId : undefined}
                    aria-autocomplete="list"
                    aria-activedescendant={isOpen && results[highlightIdx] ? `search-result-${results[highlightIdx].id}` : undefined}
                    className="search-input"
                    placeholder="Search nodes..."
                    aria-label="Search nodes (Press Ctrl+K)"
                    title="Search nodes (Press Ctrl+K)"
                    value={query}
                    onChange={(e) => { setQuery(e.target.value); setIsOpen(true); setHighlightIdx(0); }}
                    onFocus={() => setIsOpen(true)}
                    onKeyDown={handleKeyDown}
                />
                {!query && (
                    <kbd className="ghost-choice-kbd" aria-hidden="true" style={{ position: 'absolute', right: '10px', pointerEvents: 'none', background: 'var(--bg-panel)' }}>
                        Ctrl+K
                    </kbd>
                )}
                {query && (
                    <button className="search-clear" onClick={() => { setQuery(''); setIsOpen(false); }} title="Clear Search" aria-label="Clear Search"><span aria-hidden="true">✕</span></button>
                )}
            </div>

            {isOpen && results.length > 0 && (
                <div id={listboxId} role="listbox" className="search-results">
                    {results.map((node, idx) => {
                        const labelText = node.data?.file
                            ? `${node.data?.label || node.id} in ${node.data.file}`
                            : (node.data?.label || node.id);

                        return (
                            <button
                                key={node.id}
                                id={`search-result-${node.id}`}
                                role="option"
                                aria-selected={idx === highlightIdx}
                                aria-label={labelText}
                                className={`search-result-item ${idx === highlightIdx ? 'highlighted' : ''}`}
                                onClick={() => handleSelect(node)}
                                onMouseEnter={() => setHighlightIdx(idx)}
                            >
                            <span className="search-result-icon" aria-hidden="true">{typeIcon(node)}</span>
                            <div className="search-result-text">
                                <span className="search-result-label" title={node.data?.label || node.id}>{node.data?.label || node.id}</span>
                                {node.data?.file && (
                                    <span className="search-result-file" title={node.data.file}>
                                        {getShortName(node.data.file)}
                                    </span>
                                )}
                            </div>
                            </button>
                        );
                    })}
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
