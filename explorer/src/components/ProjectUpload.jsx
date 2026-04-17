import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
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
                <span aria-hidden="true">📁</span> Upload Project
            </button>

            {isModalOpen && (
                <div className="upload-modal-overlay" onClick={() => !isAnalyzing && setIsModalOpen(false)}>
                    <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="upload-modal-header">
                            <h3>Upload Project</h3>
                            <span style={{ display: 'inline-flex' }} title={isAnalyzing ? "Cannot close while analyzing project" : "Close Upload Modal"}>
                                <button
                                    className="modal-close-btn"
                                    onClick={() => setIsModalOpen(false)}
                                    disabled={isAnalyzing}
                                    aria-label="Close Upload Modal"
                                ><span aria-hidden="true">✕</span></button>
                            </span>
                        </div>

                        <div className="upload-modal-body">
                            {isAnalyzing ? (
                                <div className="analyzing-state" aria-live="polite" aria-busy="true">
                                    <div className="vibe-spinner" aria-hidden="true"></div>
                                    <p>Analyzing Project...</p>
                                    <span className="analyzing-subtitle">Building call graph, mapping vibes</span>
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
                                    style={{ position: 'relative' }}
                                >
                                    {isDragging && (
                                        <div style={{
                                            position: 'absolute', inset: 0,
                                            background: 'rgba(56, 189, 248, 0.1)',
                                            border: '2px dashed var(--color-accent-ice)',
                                            borderRadius: 'var(--radius-md)',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            color: 'var(--color-accent-ice)', fontSize: '16px', fontWeight: 600,
                                            zIndex: 10,
                                        }}>
                                            Drop files here
                                        </div>
                                    )}
                                    <div className="upload-icon" aria-hidden="true">📤</div>
                                    <p>Select a project folder to analyze</p>
                                    <span className="upload-hint">Uploads all .py files to the server</span>
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        style={{ display: 'none' }}
                                        webkitdirectory="true"
                                        directory="true"
                                        onChange={handleUpload}
                                        multiple
                                    />
                                    <button className="upload-select-btn" tabIndex={-1} aria-hidden="true">Select Folder</button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// PERFORMANCE OPTIMIZATION (Bolt):
// Wrap ProjectUpload in memo() to prevent re-renders on every tick
// of the Ghost Runner simulation, as it only receives a stable callback.
export default memo(ProjectUpload);
