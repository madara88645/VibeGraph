import React, { useCallback, useEffect, useState } from 'react';
import { useReactFlow } from 'reactflow';

import {
  fetchAiJson,
  getFriendlyAiErrorMessage,
} from '../utils/aiClient';

const LearningPath = ({
  selectedFile,
  allNodes,
  allEdges,
  onSelectNode,
  onSelectFile,
  isOpen,
  onToggle,
  apiKey,
  selectedModel,
}) => {
  const [steps, setSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { fitView } = useReactFlow();

  useEffect(() => {
    if (!isOpen || allNodes.length === 0) {
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
          body: {
            nodes: allNodes,
            edges: allEdges || [],
            selected_file: selectedFile,
            model: selectedModel || null,
          },
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
  }, [allEdges, allNodes, apiKey, isOpen, selectedFile, selectedModel]);

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

      const node = allNodes.find((candidate) => candidate.id === step.node_id);

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
    [allNodes, fitView, onSelectFile, onSelectNode, steps]
  );

  if (!isOpen) {
    return null;
  }

  const progress = steps.length > 0 ? ((currentStep + 1) / steps.length) * 100 : 0;
  const activeStep = steps[currentStep] || null;
  const activeFile = activeStep?.file_path || '';
  const fileName = activeFile.split(/[/\\]/).pop();

  return (
    <div id="learning-path-panel" className="lp-bar">
      <div className="lp-bar-icon">Target</div>

      <div className="lp-bar-main">
        <span
          style={{ display: 'inline-flex' }}
          title={loading ? 'Building learning path...' : currentStep === 0 ? 'Already at first step' : 'Previous step'}
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
            <span className="lp-bar-loading">Building learning path...</span>
          ) : error ? (
            <span className="lp-bar-error">{error}</span>
          ) : steps.length > 0 ? (
            <>
              <span className="lp-bar-step">
                Step {currentStep + 1}/{steps.length}:
              </span>
              <span className="lp-bar-node">
                {activeStep.node_name || activeStep.node_id}
              </span>
              {fileName ? <span className="lp-bar-file">{fileName}</span> : null}
              {activeStep.reason ? (
                <span className="lp-bar-reason">{activeStep.reason}</span>
              ) : null}
            </>
          ) : (
            <span className="lp-bar-empty">
              {allNodes.length === 0 ? 'Upload a project to build a learning path' : 'No path generated.'}
            </span>
          )}
        </div>

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
