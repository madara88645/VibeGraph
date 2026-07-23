import React, { memo, useState, useEffect, useCallback } from 'react';

import { IconCheck, IconDot, IconGhost } from './icons';

const GhostTutorialPanel = ({ ghostTutorial, stepSummaries = [], totalNodes, showTutorial = true, onClose }) => {
    const shouldShow = showTutorial && ghostTutorial && totalNodes > 0;

    const [isDismissed, setIsDismissed] = useState(!shouldShow);
    const [isRendered, setIsRendered] = useState(shouldShow);


    const handleClose = useCallback(() => {
        setIsDismissed(true);
        if (onClose) {
            onClose();
        } else {
            setTimeout(() => {
                setIsRendered(false);
            }, 250);
        }
    }, [onClose]);

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Escape') {
                if (e.ctrlKey || e.metaKey || e.altKey) return;
                if (['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;
                handleClose();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleClose]);

    useEffect(() => {
        let activeTimer;
        let activeTransitionTimer;

        if (shouldShow) {
            activeTimer = setTimeout(() => {
                setIsDismissed(false);
                setIsRendered(true);
            }, 0);
        } else {
            activeTimer = setTimeout(() => {
                setIsDismissed(true);
                activeTransitionTimer = setTimeout(() => {
                    setIsRendered(false);
                }, 250);
            }, 0);
        }

        return () => {
            clearTimeout(activeTimer);
            clearTimeout(activeTransitionTimer);
        };
    }, [shouldShow]);

    if (!isRendered) return null;

    const { runState, currentPhase, acceptance, progressLabel, isComplete } = ghostTutorial || {};


    return (
        <section
            className={`ghost-tutorial-panel ghost-tutorial-${runState} ${isDismissed ? 'dismissed' : ''}`}
            aria-label="Ghost Runner guided tour"
        >
            <button 
                className="ghost-tutorial-close-btn" 
                onClick={handleClose}
                aria-label="Close guided tour (Press Esc)"
                title="Close guided tour (Press Esc)"
            >
                <svg aria-hidden="true" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>

            <header className="ghost-tutorial-header">
                <span className="ghost-tutorial-badge" aria-hidden="true">
                    {isComplete ? <IconCheck size={15} /> : <IconGhost size={16} />}
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
                            {item.met
                                ? <IconCheck className="ghost-tutorial-check-icon" size={12} />
                                : <IconDot className="ghost-tutorial-check-icon" size={12} />}
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
