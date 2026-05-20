import React, { memo, useEffect } from 'react';

import { getShortName } from '../utils/stringUtils';

const GhostChoices = ({ availableNextNodes, onChoose, isPlaying, mode }) => {
    useEffect(() => {
        if (mode !== 'explore' || !isPlaying || !availableNextNodes || availableNextNodes.length === 0) return;

        const handleKeyDown = (e) => {
            if (e.ctrlKey || e.metaKey || e.altKey) return;
            if (['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;
            const num = parseInt(e.key, 10);
            if (!isNaN(num) && num > 0 && num <= availableNextNodes.length) {
                onChoose(availableNextNodes[num - 1].id);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [availableNextNodes, onChoose, isPlaying, mode]);

    if (mode !== 'explore' || !isPlaying || !availableNextNodes || availableNextNodes.length === 0) {
        return null;
    }

    return (
        <div className="ghost-choices" role="navigation" aria-label="Ghost runner next node choices">
            <div className="ghost-choices-title">Where should the ghost go next?</div>
            {availableNextNodes.map((node, index) => {
                const titleText = `Go to ${node.data?.label || node.id}${node.data?.file ? ` (${getShortName(node.data.file)})` : ''}`;
                return (
                <button
                    key={node.id}
                    className="ghost-choice-btn"
                    onClick={() => onChoose(node.id)}
                    title={titleText}
                    aria-label={titleText}
                >
                    <span className="ghost-choice-label">
                        <span aria-hidden="true">
                            {node.data?.type === 'class' ? '\uD83C\uDFD7\uFE0F' : node.data?.entry_point ? '\uD83D\uDE80' : '\u26A1'}
                        </span>
                        <span className="ghost-choice-text">{node.data?.label || node.id}</span>
                        {index < 9 && (
                            <kbd className="ghost-choice-kbd" aria-hidden="true">
                                {index + 1}
                            </kbd>
                        )}
                    </span>
                </button>
                );
            })}
        </div>
    );
};

// Wrap GhostChoices in memo() to prevent unnecessary re-renders
export default memo(GhostChoices);
