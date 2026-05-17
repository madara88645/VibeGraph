import React, { memo } from 'react';

const GhostTutorialPanel = ({ ghostTutorial, stepSummaries = [], totalNodes }) => {
    if (!ghostTutorial || totalNodes === 0) {
        return null;
    }

    const { runState, currentPhase, acceptance, progressLabel, isComplete } = ghostTutorial;

    return (
        <section
            className={`ghost-tutorial-panel ghost-tutorial-${runState}`}
            aria-label="Ghost Runner guided tour"
        >
            <header className="ghost-tutorial-header">
                <span className="ghost-tutorial-badge" aria-hidden="true">
                    {isComplete ? '✓' : '👻'}
                </span>
                <div>
                    <div className="ghost-tutorial-progress">{progressLabel}</div>
                    {isComplete ? (
                        <p className="ghost-tutorial-lead">
                            You have walked the basics: start, follow steps, branch across files when
                            available, and pause to read the recap below.
                        </p>
                    ) : (
                        <>
                            <h3 className="ghost-tutorial-title">{currentPhase?.title}</h3>
                            <p className="ghost-tutorial-lead">{currentPhase?.summary}</p>
                        </>
                    )}
                </div>
            </header>

            {!isComplete && acceptance.length > 0 && (
                <ul className="ghost-tutorial-checklist" aria-label="Tour acceptance criteria">
                    {acceptance.map(item => (
                        <li key={item.id} className={item.met ? 'ghost-tutorial-check met' : 'ghost-tutorial-check'}>
                            <span className="ghost-tutorial-check-icon" aria-hidden="true">
                                {item.met ? '✓' : '○'}
                            </span>
                            {item.label}
                        </li>
                    ))}
                </ul>
            )}

            {stepSummaries.length > 0 && (
                <div className="ghost-tutorial-steps">
                    <h4 className="ghost-tutorial-steps-title">Recent ghost steps</h4>
                    <ol className="ghost-tutorial-step-list" reversed>
                        {stepSummaries.map(entry => (
                            <li key={`${entry.step}-${entry.label}`}>
                                <span className="ghost-tutorial-step-num">Step {entry.step}</span>
                                <span className="ghost-tutorial-step-label">{entry.label}</span>
                            </li>
                        ))}
                    </ol>
                </div>
            )}
        </section>
    );
};

export default memo(GhostTutorialPanel);
