import React, { memo } from 'react';

const GhostChoices = ({ availableNextNodes, onChoose, isPlaying, mode }) => {
    if (mode !== 'explore' || !isPlaying || !availableNextNodes || availableNextNodes.length === 0) {
        return null;
    }

    return (
        <div className="ghost-choices" role="navigation" aria-label="Ghost runner next node choices">
            <div className="ghost-choices-title">Where should the ghost go next?</div>
            {availableNextNodes.map(node => (
                <button
                    key={node.id}
                    className="ghost-choice-btn"
                    onClick={() => onChoose(node.id)}
                    title={`Go to ${node.data?.label || node.id}${node.data?.file ? ` (${node.data.file.split(/[/\\]/).pop()})` : ''}`}
                >
                    <span className="ghost-choice-label">
                        <span aria-hidden="true">
                            {node.data?.type === 'class' ? '\uD83C\uDFD7\uFE0F' : node.data?.entry_point ? '\uD83D\uDE80' : '\u26A1'}
                        </span>
                        {node.data?.label || node.id}
                    </span>
                </button>
            ))}
        </div>
    );
};

// Wrap GhostChoices in memo() to prevent unnecessary re-renders
export default memo(GhostChoices);
