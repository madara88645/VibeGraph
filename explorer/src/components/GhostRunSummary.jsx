import React, { memo } from 'react';

const GhostRunSummary = ({ runSummary, isPlaying }) => {
    // Show summary only when paused and there's data
    if (isPlaying || !runSummary || runSummary.visitedCount === 0) return null;

    const {
        visitedCount,
        totalNodes,
        filesVisited,
        mostConnected,
        unvisitedEntries,
        guidedTourComplete,
        recentSteps = [],
    } = runSummary;
    const coveragePercent = totalNodes > 0 ? Math.round((visitedCount / totalNodes) * 100) : 0;

    return (
        <div className="ghost-run-summary" role="status" aria-label="Ghost runner summary">
            <h4 className="ghost-summary-title">Run summary</h4>
            {guidedTourComplete ? (
                <p className="ghost-summary-tour-done" role="status">
                    Guided tour complete — you started the ghost, followed steps, branched across files when
                    the graph allowed it, and paused here to review.
                </p>
            ) : null}
            <div className="ghost-summary-stats">
                <span className="ghost-summary-stat">
                    <strong>{visitedCount}</strong> of <strong>{totalNodes}</strong> code nodes visited (
                    {coveragePercent}% coverage)
                </span>
                <span className="ghost-summary-stat">
                    <strong>{filesVisited}</strong> distinct files touched
                </span>
                {mostConnected && (
                    <span className="ghost-summary-stat">
                        Busiest hub: <strong>{mostConnected.label}</strong> ({mostConnected.degree} edges)
                    </span>
                )}
            </div>
            {recentSteps.length > 0 && (
                <div className="ghost-summary-steps" aria-label="Last visited nodes this run">
                    <h5 className="ghost-summary-subhead">Where you just were</h5>
                    <ol className="ghost-summary-step-list">
                        {recentSteps.map(entry => (
                            <li key={`${entry.step}-${entry.label}`}>
                                <span className="ghost-summary-step-num">Step {entry.step}</span>
                                <span className="ghost-summary-step-name">{entry.label}</span>
                            </li>
                        ))}
                    </ol>
                </div>
            )}
            {unvisitedEntries.length > 0 && (
                <div className="ghost-summary-entries">
                    Entry points not visited this run: {unvisitedEntries.join(', ')}
                </div>
            )}
        </div>
    );
};

// Wrap GhostRunSummary in memo() to prevent unnecessary re-renders
export default memo(GhostRunSummary);
