import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useReactFlow } from 'reactflow';

import {
  fetchAiJsonWithRetry,
  getFriendlyAiErrorMessage,
} from '../utils/aiClient';
import { getShortName } from '../utils/stringUtils';

const LearningPath = ({
  selectedFile,
  allNodes,
  allNodesMap,
  allEdges,
  onSelectNode,
  onSelectFile,
  isOpen,
  onToggle,
  apiKey,
  selectedModel,
  topOffset = 84,
}) => {
  const [steps, setSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { fitView } = useReactFlow();

  const [isRendered, setIsRendered] = useState(isOpen);
  const [isDismissed, setIsDismissed] = useState(!isOpen);

  useEffect(() => {
    if (isOpen) {
      setIsRendered(true);
      const timer = setTimeout(() => setIsDismissed(false), 20);
      return () => clearTimeout(timer);
    } else {
      setIsDismissed(true);
      const timer = setTimeout(() => setIsRendered(false), 300); // match transition
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  // Monotonic id so a superseded or unmounted request never applies its result.
  const requestIdRef = useRef(0);

  const runFetch = useCallback(async () => {
    const requestId = (requestIdRef.current += 1);
    setLoading(true);
    setError(null);
    setSteps([]);
    setCurrentStep(0);

    try {
      // fetchAiJsonWithRetry silently retries transient gateway errors (e.g. a
      // Fly.io cold-start 503) before surfacing failure to the user.
      const data = await fetchAiJsonWithRetry('/api/learning-path', {
        apiKey,
        body: {
          nodes: allNodes,
          edges: allEdges || [],
          selected_file: selectedFile,
          model: selectedModel || null,
        },
      });

      if (requestIdRef.current !== requestId) {
        return;
      }
      if (data.steps && data.steps.length > 0) {
        setSteps(data.steps);
      }
    } catch (requestError) {
      if (requestIdRef.current !== requestId) {
        return;
      }
      setError(getFriendlyAiErrorMessage(requestError, 'Could not build learning path.'));
    } finally {
      if (requestIdRef.current === requestId) {
        setLoading(false);
      }
    }
  }, [allEdges, allNodes, apiKey, selectedFile, selectedModel]);

  useEffect(() => {
    if (!isOpen || allNodes.length === 0) {
      return undefined;
    }

    runFetch();

    return () => {
      // Invalidate any in-flight request when inputs change or the panel closes.
      requestIdRef.current += 1;
    };
  }, [isOpen, allNodes, runFetch]);

  const goToStep = useCallback(
    (idx) => {
      if (idx < 0 || idx >= steps.length) {
        return;
      }
      setCurrentStep(idx);

      const step = steps[idx];
      if (!step) {
        return;
      }

      // PERFORMANCE OPTIMIZATION (Bolt): Replaced O(N) array find() with O(1) Map lookup
      // to eliminate functional callback overhead and array traversal.
      const node = allNodesMap ? allNodesMap.get(step.node_id) : allNodes.find((candidate) => candidate.id === step.node_id);

      if (node) {
        const nextFile = step.file_path || node.data?.file;
        if (nextFile) {
          onSelectFile(nextFile);
        }
        onSelectNode(node);

        setTimeout(() => {
          fitView({
            nodes: [node],
            duration: 800,
            padding: 2.0,
          });
        }, 50);
      }
    },
    [allNodes, allNodesMap, fitView, onSelectFile, onSelectNode, steps]
  );

  if (!isRendered) {
    return null;
  }

  const progress = steps.length > 0 ? ((currentStep + 1) / steps.length) * 100 : 0;
  const activeStep = steps[currentStep] || null;
  const activeFile = activeStep?.file_path || '';
  const fileName = getShortName(activeFile);
  const activeNodeName = activeStep?.node_name || activeStep?.node_id || '';
  const hasStepContent = !loading && !error && steps.length > 0 && activeStep;

  return (
    <div
      id="learning-path-panel"
      className={`lp-bar ${isDismissed ? 'dismissed' : ''}`}
      style={{ top: `${topOffset}px` }}
    >
      <div className="lp-bar-row lp-bar-row-top">
        <div className="lp-bar-heading">
          <span className="lp-bar-icon">Target</span>
          <span className="lp-bar-title">Learning Path</span>
        </div>

        <div className="lp-bar-controls" data-testid="learning-path-controls">
          <span className="lp-bar-step">
            {steps.length > 0 && !loading && !error
              ? `Step ${currentStep + 1} of ${steps.length}`
              : 'Path status'}
          </span>

          <span
            style={{ display: 'inline-flex' }}
            title={loading ? 'Building learning path...' : currentStep === 0 ? 'Already at first step' : 'Previous step'}
          >
            <button
              className="lp-bar-nav"
              onClick={() => goToStep(currentStep - 1)}
              disabled={currentStep === 0 || loading}
              aria-label="Previous step"
            >
              {loading ? (
                <span
                  className="vibe-spinner"
                  style={{ width: '12px', height: '12px', borderWidth: '2px' }}
                  aria-hidden="true"
                />
              ) : (
                <span aria-hidden="true">{'<'}</span>
              )}
            </button>
          </span>

          <span
            style={{ display: 'inline-flex' }}
            title={
              loading
                ? 'Building learning path...'
                : currentStep === steps.length - 1
                  ? 'Already at last step'
                  : 'Next step'
            }
          >
            <button
              className="lp-bar-nav"
              onClick={() => goToStep(currentStep + 1)}
              disabled={currentStep === steps.length - 1 || loading || steps.length === 0}
              aria-label="Next step"
            >
              {loading ? (
                <span
                  className="vibe-spinner"
                  style={{ width: '12px', height: '12px', borderWidth: '2px' }}
                  aria-hidden="true"
                />
              ) : (
                <span aria-hidden="true">{'>'}</span>
              )}
            </button>
          </span>

          <button
            className="lp-bar-close"
            onClick={onToggle}
            title="Close Learning Path"
            aria-label="Close Learning Path"
          >
            <span aria-hidden="true">x</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="lp-bar-status">
          <span className="lp-bar-loading">Building learning path...</span>
        </div>
      ) : error ? (
        <div className="lp-bar-status">
          <span className="lp-bar-error">{error}</span>
          <button
            type="button"
            className="lp-bar-retry"
            onClick={runFetch}
            aria-label="Retry building learning path"
          >
            Retry
          </button>
        </div>
      ) : hasStepContent ? (
        <>
          <div className="lp-bar-row lp-bar-row-meta" data-testid="learning-path-metadata">
            <div className="lp-bar-meta-block">
              <span className="lp-bar-meta-label">Node</span>
              <span className="lp-bar-node" title={activeNodeName}>
                {activeNodeName}
              </span>
            </div>

            {fileName ? (
              <div className="lp-bar-meta-block">
                <span className="lp-bar-meta-label">File</span>
                <span className="lp-bar-file" title={activeFile || fileName}>
                  {fileName}
                </span>
              </div>
            ) : null}
          </div>

          <div
            className="lp-bar-row lp-bar-row-description"
            data-testid="learning-path-description"
            title={activeStep.reason || ''}
          >
            {activeStep.reason ? (
              <span className="lp-bar-reason">{activeStep.reason}</span>
            ) : (
              <span className="lp-bar-empty">No explanation available for this step yet.</span>
            )}
          </div>
        </>
      ) : (
        <div className="lp-bar-status">
          <span className="lp-bar-empty">
            {allNodes.length === 0 ? 'Upload a project to build a learning path' : 'No path generated.'}
          </span>
        </div>
      )}

      {steps.length > 0 ? (
        <div
          className="lp-bar-progress"
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Learning path progress"
        >
          <div className="lp-bar-progress-fill" style={{ width: `${progress}%` }} />
        </div>
      ) : null}
    </div>
  );
};

export default React.memo(LearningPath);
