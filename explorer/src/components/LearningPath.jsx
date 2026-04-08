import React, { useCallback, useEffect, useState } from 'react';
import { useReactFlow } from 'reactflow';

import {
  ensureAiReady,
  fetchAiJson,
  getFriendlyAiErrorMessage,
} from '../utils/aiClient';

const LearningPath = ({
  selectedFile,
  allNodes,
  onSelectNode,
  onSelectFile,
  isOpen,
  onToggle,
  apiKey,
  selectedModel,
  aiReady,
  onOpenAiSettings,
}) => {
  const [steps, setSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { fitView } = useReactFlow();

  useEffect(() => {
    if (!isOpen || !selectedFile) {
      return;
    }

    if (
      !ensureAiReady(
        aiReady,
        onOpenAiSettings,
        'Open AI Settings and add your OpenRouter key to build a learning path.'
      )
    ) {
      setSteps([]);
      setCurrentStep(0);
      setLoading(false);
      setError('Open AI Settings and add your OpenRouter key.');
      return;
    }

    const fetchPath = async () => {
      setLoading(true);
      setError(null);
      setSteps([]);
      setCurrentStep(0);

      try {
        const data = await fetchAiJson('/api/learning-path', {
          apiKey,
          body: { file_path: selectedFile, model: selectedModel || null },
        });

        if (data.steps && data.steps.length > 0) {
          setSteps(data.steps);
        } else {
          setError('No steps found.');
        }
      } catch (requestError) {
        setError(getFriendlyAiErrorMessage(requestError, 'Could not build learning path.'));
      } finally {
        setLoading(false);
      }
    };

    fetchPath();
  }, [aiReady, apiKey, isOpen, onOpenAiSettings, selectedFile, selectedModel]);

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

      const node = allNodes.find(
        (candidate) =>
          candidate.id === step.node_id || candidate.data?.label === step.node_name
      );

      if (node) {
        if (node.data?.file) {
          onSelectFile(node.data.file);
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
    [allNodes, fitView, onSelectFile, onSelectNode, steps]
  );

  if (!isOpen) {
    return null;
  }

  const progress = steps.length > 0 ? ((currentStep + 1) / steps.length) * 100 : 0;

  return (
    <div id="learning-path-panel" className="lp-bar">
      <div className="lp-bar-icon">Target</div>

      <div className="lp-bar-main">
        <span
          style={{ display: 'inline-flex' }}
          title={loading ? 'Analyzing file...' : currentStep === 0 ? 'Already at first step' : 'Previous step'}
        >
          <button
            className="lp-bar-nav"
            onClick={() => goToStep(currentStep - 1)}
            disabled={currentStep === 0 || loading}
            aria-label="Previous Step"
          >
            <span aria-hidden="true">{'<'}</span>
          </button>
        </span>

        <div className="lp-bar-info">
          {loading ? (
            <span className="lp-bar-loading">Analyzing file...</span>
          ) : error ? (
            <span className="lp-bar-error">{error}</span>
          ) : steps.length > 0 ? (
            <>
              <span className="lp-bar-step">
                Step {currentStep + 1}/{steps.length}:
              </span>
              <span className="lp-bar-node">
                {steps[currentStep].node_name || steps[currentStep].node_id}
              </span>
            </>
          ) : (
            <span className="lp-bar-empty">No steps</span>
          )}
        </div>

        <span
          style={{ display: 'inline-flex' }}
          title={
            loading
              ? 'Analyzing file...'
              : currentStep === steps.length - 1
                ? 'Already at last step'
                : 'Next step'
          }
        >
          <button
            className="lp-bar-nav"
            onClick={() => goToStep(currentStep + 1)}
            disabled={currentStep === steps.length - 1 || loading || steps.length === 0}
            aria-label="Next Step"
          >
            <span aria-hidden="true">{'>'}</span>
          </button>
        </span>
      </div>

      <button
        className="lp-bar-close"
        onClick={onToggle}
        title="Close Learning Path"
        aria-label="Close Learning Path"
      >
        <span aria-hidden="true">x</span>
      </button>

      {steps.length > 0 ? (
        <div className="lp-bar-progress">
          <div className="lp-bar-progress-fill" style={{ width: `${progress}%` }} />
        </div>
      ) : null}
    </div>
  );
};

export default React.memo(LearningPath);
