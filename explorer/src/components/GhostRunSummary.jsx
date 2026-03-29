import React, { memo } from 'react';

const GhostRunSummary = ({ runSummary, isPlaying }) => {
    // Show summary only when paused and there's data
    if (isPlaying || !runSummary || runSummary.visitedCount === 0) return null;

    const { visitedCount, totalNodes, filesVisited, mostConnected, unvisitedEntries } = runSummary;
    const coveragePercent = totalNodes > 0 ? Math.round((visitedCount / totalNodes) * 100) : 0;

    return (
        <div className="ghost-run-summary" role="status" aria-label="Ghost runner summary">
            <h4 className="ghost-summary-title">Run Summary</h4>
            <div className="ghost-summary-stats">
                <span className="ghost-summary-stat">
                    <strong>{visitedCount}</strong>/{totalNodes} nodes ({coveragePercent}%)
                </span>
                <span className="ghost-summary-stat">
                    <strong>{filesVisited}</strong> files
                </span>
                {mostConnected && (
                    <span className="ghost-summary-stat">
                        Hub: <strong>{mostConnected.label}</strong> ({mostConnected.degree} connections)
                    </span>
                )}
            </div>
            {unvisitedEntries.length > 0 && (
                <div className="ghost-summary-entries">
                    Unvisited entry points: {unvisitedEntries.join(', ')}
                </div>
            )}
        </div>
    );
};

// Wrap GhostRunSummary in memo() to prevent unnecessary re-renders
export default memo(GhostRunSummary);
