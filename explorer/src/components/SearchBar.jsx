import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useReactFlow } from 'reactflow';

import { getShortName } from '../utils/stringUtils';
import { IconClass, IconClose, IconEntry, IconFunction, IconSearch } from './icons';

// WeakMap to cache computed search strings without mutating the original node objects
const searchCache = new WeakMap();

const FOCUS_ZOOM = 1.5;
const FOCUS_DURATION_MS = 600;
// Comfortably past the pan animation, so a mid-flight zoom is never mistaken
// for an override.
const FOCUS_REASSERT_DELAY_MS = 900;
const MAX_FOCUS_REASSERTS = 2;
const ZOOM_EPSILON = 0.01;
// Below this width the explanation panel is a bottom sheet (see the
// max-width: 768px block in index.css), so it covers nothing on the right.
const PANEL_SHEET_BREAKPOINT_PX = 768;

// Width of the canvas the explanation panel will cover once a result is
// selected. Read from the same custom properties the panel is laid out with so
// the two cannot drift apart.
function getRightOcclusion() {
    if (typeof window === 'undefined' || window.innerWidth <= PANEL_SHEET_BREAKPOINT_PX) {
        return 0;
    }
    const rootStyle = getComputedStyle(document.documentElement);
    const readPx = (name) => parseFloat(rootStyle.getPropertyValue(name)) || 0;
    return readPx('--explanation-panel-width') + readPx('--explanation-panel-edge-offset');
}

const SearchBar = ({ allNodes, onSelectNode, onSelectFile }) => {
    const [query, setQuery] = useState('');
    const [isOpen, setIsOpen] = useState(false);
    const [highlightIdx, setHighlightIdx] = useState(0);
    const inputRef = useRef(null);
    const containerRef = useRef(null);
    const { getNode, setCenter, getViewport } = useReactFlow();

    // Keyboard shortcut: Ctrl+K or /
    useEffect(() => {
        const handler = (e) => {
            if (((e.ctrlKey || e.metaKey) && e.key === 'k') || (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName))) {
                e.preventDefault();
                inputRef.current?.focus();
                // Select any existing text so new typing replaces it instead of appending
                inputRef.current?.select();
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
        // Picking a node in another file triggers a dagre re-layout (useGraphData)
        // that repositions nodes. The `node` from `allNodes` carries a stale
        // pre-relayout position, so centering on it drifts the camera to empty
        // space (#460). Wait until the node lands in the post-relayout store, then
        // center on its current laid-out position.
        let attempts = 0;
        let reasserts = 0;
        const focusNode = () => {
            const laidOut = getNode(node.id);
            const position = laidOut?.positionAbsolute || laidOut?.position;
            if (position) {
                const width = laidOut.width ?? 172;
                const height = laidOut.height ?? 36;
                // Selecting a result also opens the explanation panel over the
                // right edge of the canvas, so centering in the FULL viewport
                // drops the node behind it (#560). Shift the target by half the
                // covered strip to center it in the part still visible.
                setCenter(
                    position.x + width / 2 + getRightOcclusion() / 2 / FOCUS_ZOOM,
                    position.y + height / 2,
                    {
                        zoom: FOCUS_ZOOM,
                        duration: FOCUS_DURATION_MS,
                    }
                );
                // A result in another file swaps the whole node set, and React
                // Flow re-fits the view for it — after this call, throwing away
                // the camera we just set (#566). Re-assert once the swap has
                // settled, but only when the viewport really was overridden, so
                // a user who deliberately zoomed away is never fought.
                if (reasserts++ < MAX_FOCUS_REASSERTS) {
                    setTimeout(() => {
                        const viewport = getViewport?.();
                        if (viewport && Math.abs(viewport.zoom - FOCUS_ZOOM) > ZOOM_EPSILON) {
                            focusNode();
                        }
                    }, FOCUS_REASSERT_DELAY_MS);
                }
            } else if (attempts++ < 30) {
                setTimeout(focusNode, 16);
            }
        };
        focusNode();
        setIsOpen(false);
        setQuery('');
    }, [onSelectFile, onSelectNode, getNode, setCenter, getViewport]);

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
        if (node.data?.entry_point) return IconEntry;
        if (node.data?.type === 'class') return IconClass;
        return IconFunction;
    };

    const listboxId = "search-results-listbox";

    return (
        <div className="search-bar" ref={containerRef}>
            <div className="search-input-wrapper">
                <label htmlFor="search-input" style={{ position: 'absolute', width: '1px', height: '1px', padding: '0', margin: '-1px', overflow: 'hidden', clip: 'rect(0, 0, 0, 0)', whiteSpace: 'nowrap', border: '0' }}>
                    Search nodes (Ctrl+K)
                </label>
                <IconSearch className="search-icon" size={14} />
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
                    <button className="search-clear" onClick={() => { setQuery(''); setIsOpen(false); }} title="Clear Search" aria-label="Clear Search"><IconClose size={13} /></button>
                )}
            </div>

            {isOpen && results.length > 0 && (
                <div id={listboxId} role="listbox" className="search-results">
                    {results.map((node, idx) => {
                        const ResultIcon = typeIcon(node);
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
                            <ResultIcon className="search-result-icon" size={15} />
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
