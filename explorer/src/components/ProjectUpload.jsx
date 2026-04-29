import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import { createPortal } from 'react-dom';
import { useToast } from '../hooks/useToast';

const EMPTY_GRAPH_MESSAGE = 'No analyzable Python code found.';
const NETWORK_ERROR_MESSAGE = 'Backend is not reachable. Start the backend or check deployment.';

async function readUploadError(response) {
    try {
        const payload = await response.json();
        if (typeof payload?.detail === 'string') {
            return payload.detail;
        }
    } catch {
        // Fall back to the status text below when the backend sends no JSON body.
    }

    return response.statusText || `HTTP ${response.status}`;
}

function getUploadErrorMessage(error) {
    if (error instanceof TypeError && /failed to fetch|network/i.test(error.message)) {
        return NETWORK_ERROR_MESSAGE;
    }
    return error?.message || 'Unknown upload error.';
}

function validateGraphResult(result) {
    if (!Array.isArray(result?.nodes) || !Array.isArray(result?.edges)) {
        throw new Error('Analysis completed but graph data is missing.');
    }

    if (result.nodes.length === 0) {
        throw new Error(EMPTY_GRAPH_MESSAGE);
    }

    return result;
}

const ProjectUpload = ({ onUploadSuccess }) => {
    const showToast = useToast();
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef(null);

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Escape' && isModalOpen && !isAnalyzing) {
                setIsModalOpen(false);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isModalOpen, isAnalyzing]);

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDragEnter = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const uploadFiles = useCallback(async (files, getPath) => {
        if (!files || files.length === 0) return;

        setIsAnalyzing(true);
        const formData = new FormData();

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            formData.append('files', file, getPath(file));
        }

        try {
            const response = await fetch('/api/upload-project', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(await readUploadError(response));
            }

            const result = validateGraphResult(await response.json());
            if (onUploadSuccess) onUploadSuccess(result);
            setIsModalOpen(false);
            showToast('Project analyzed successfully!', 'success');
        } catch (error) {
            console.error("Project upload failed:", error);
            showToast(`Upload failed: ${getUploadErrorMessage(error)}`, 'error');
        } finally {
            setIsAnalyzing(false);
            // Reset input so the same folder can be uploaded again if needed.
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    }, [onUploadSuccess, showToast]);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback(async (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (!files.length) return;

        await uploadFiles(files, (file) => file.webkitRelativePath || file.name);
    }, [uploadFiles]);

    const handleUpload = async (event) => {
        const files = event.target.files;
        if (!files || files.length === 0) return;

        await uploadFiles(files, (file) => file.webkitRelativePath || file.name);
    };

    return (
        <div className="project-upload-container">
            <button
                className="header-action-btn upload-btn"
                onClick={() => setIsModalOpen(true)}
                title="Upload new project for analysis"
                aria-label="Upload new project for analysis"
            >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ opacity: 0.75, marginRight: '2px' }}>
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                </svg>
                Upload Project
            </button>

            {isModalOpen && createPortal(
                <div className="upload-modal-overlay" onClick={() => !isAnalyzing && setIsModalOpen(false)}>
                    <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
                        <span
                            className="modal-close-wrapper"
                            style={{ display: 'inline-flex' }}
                            title={isAnalyzing ? "Cannot close while analyzing project" : "Close"}
                        >
                            <button
                                className="modal-close-btn"
                                onClick={() => setIsModalOpen(false)}
                                disabled={isAnalyzing}
                                aria-label="Close Upload Modal"
                            >
                                <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                                    <path d="M4 4l8 8M12 4l-8 8" />
                                </svg>
                            </button>
                        </span>

                        {isAnalyzing ? (
                            <div className="analyzing-state" aria-live="polite" aria-busy="true">
                                <div className="vibe-spinner" aria-hidden="true"></div>
                                <p>Analyzing project…</p>
                                <span className="analyzing-subtitle">Building call graph</span>
                            </div>
                        ) : (
                            <div
                                className={`upload-zone ${isDragging ? 'upload-zone-dragging' : ''}`}
                                onClick={() => fileInputRef.current?.click()}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' || e.key === ' ') {
                                        e.preventDefault();
                                        fileInputRef.current?.click();
                                    }
                                }}
                                onDragOver={handleDragOver}
                                onDragEnter={handleDragEnter}
                                onDragLeave={handleDragLeave}
                                onDrop={handleDrop}
                                tabIndex={0}
                                role="button"
                                aria-label="Select a project folder to analyze"
                            >
                                {isDragging && (
                                    <div className="upload-zone-drop-indicator">
                                        <span>Drop to upload</span>
                                    </div>
                                )}

                                <div className="upload-content-wrapper">
                                    <svg className="upload-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                        <polyline points="17 8 12 3 7 8" />
                                        <line x1="12" y1="3" x2="12" y2="15" />
                                    </svg>
                                    <div className="upload-text-container">
                                        <h2>Upload your project</h2>
                                        <p className="upload-hint">Drop your Python project folder here, or browse</p>
                                    </div>
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        style={{ display: 'none' }}
                                        webkitdirectory="true"
                                        directory="true"
                                        onChange={handleUpload}
                                        multiple
                                    />
                                    <button className="upload-select-btn" tabIndex={-1} aria-hidden="true">Browse files</button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>,
                document.body
            )}
        </div>
    );
};

// PERFORMANCE OPTIMIZATION (Bolt):
// Wrap ProjectUpload in memo() to prevent re-renders on every tick
// of the Ghost Runner simulation, as it only receives a stable callback.
export default memo(ProjectUpload);
