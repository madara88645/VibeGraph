import React, { useState, useEffect, useRef, memo } from 'react';

const GhostNarration = ({ narration, isPlaying }) => {
    const [visible, setVisible] = useState(false);
    const [displayText, setDisplayText] = useState('');
    const [enabled, setEnabled] = useState(true);
    const prevNarrationRef = useRef(null);

    // Typewriter effect
    useEffect(() => {
        if (!narration?.narration || !enabled || narration === prevNarrationRef.current) return;
        prevNarrationRef.current = narration;

        const text = narration.narration;
        setDisplayText('');
        setVisible(true);

        let i = 0;
        const interval = setInterval(() => {
            i++;
            setDisplayText(text.slice(0, i));
            if (i >= text.length) clearInterval(interval);
        }, 18);

        return () => clearInterval(interval);
    }, [narration, enabled]);

    // Hide when ghost stops
    useEffect(() => {
        if (!isPlaying) {
            const timeout = setTimeout(() => setVisible(false), 1500);
            return () => clearTimeout(timeout);
        }
    }, [isPlaying]);

    if (!enabled || !visible || !displayText) return null;

    const importanceColor = {
        high: 'var(--accent-ghost)',
        medium: 'var(--color-accent-ice)',
        low: 'var(--text-muted)',
    };

    return (
        <div className="ghost-narration" role="status" aria-live="polite">
            <div className="ghost-narration-content">
                <span className="ghost-narration-text">{displayText}</span>
                {narration?.relationship && (
                    <span className="ghost-narration-rel">{narration.relationship}</span>
                )}
            </div>
            <div className="ghost-narration-meta">
                {narration?.importance && (
                    <span
                        className="ghost-narration-importance"
                        style={{ color: importanceColor[narration.importance] || importanceColor.medium }}
                    >
                        {narration.importance === 'high' ? '!!' : narration.importance === 'medium' ? '!' : ''}
                    </span>
                )}
                <button
                    className="ghost-narration-toggle"
                    onClick={() => { setEnabled(false); setVisible(false); }}
                    title="Disable narration"
                    aria-label="Disable ghost narration"
                >
                    <span aria-hidden="true">✕</span>
                </button>
            </div>
        </div>
    );
};

// Wrap GhostNarration in memo() to prevent unnecessary re-renders
export default memo(GhostNarration);
