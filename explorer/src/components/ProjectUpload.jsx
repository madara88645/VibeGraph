import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import { createPortal } from 'react-dom';
import { useToast } from '../hooks/useToast';

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

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i], files[i].name);
        }

        setIsAnalyzing(true);
        try {
            const response = await fetch('/api/upload-project', { method: 'POST', body: formData });
            if (!response.ok) throw new Error(`Upload failed: ${response.status}`);
            const result = await response.json();
            if (onUploadSuccess) onUploadSuccess(result);
            showToast('Project uploaded successfully!', 'success');
            setIsModalOpen(false);
        } catch (err) {
            showToast(`Upload failed: ${err.message}`, 'error');
        } finally {
            setIsAnalyzing(false);
        }
    }, [onUploadSuccess, showToast]);

    const handleUpload = async (event) => {
        const files = event.target.files;
        if (!files || files.length === 0) return;

        setIsAnalyzing(true);
        const formData = new FormData();

        // Append all files to the form data
        // For folder upload, the relative path is critical for the backend to map files correctly
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const path = file.webkitRelativePath || file.name;
            formData.append('files', file, path);
        }

        try {
            const response = await fetch('/api/upload-project', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const result = await response.json();

            // Expected backend result should follow the standard graph JSON structure
            if (result.nodes && result.edges) {
                onUploadSuccess(result);
                setIsModalOpen(false);
                showToast('Project analyzed successfully!', 'success');
            } else {
                console.error("Analysis success but invalid graph data returned", result);
                showToast('Analysis completed but graph data is missing.', 'error');
            }
        } catch (error) {
            console.error("Project upload failed:", error);
            showToast(`Upload failed: ${error.message}`, 'error');
        } finally {
            setIsAnalyzing(false);
            // Reset input so the same folder can be uploaded again if needed
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
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
                        <button
                            className="modal-close-btn"
                            onClick={() => setIsModalOpen(false)}
                            disabled={isAnalyzing}
                            aria-label="Close Upload Modal"
                            title={isAnalyzing ? "Cannot close while analyzing project" : "Close"}
                        >
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                                <path d="M4 4l8 8M12 4l-8 8" />
                            </svg>
                        </button>

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
