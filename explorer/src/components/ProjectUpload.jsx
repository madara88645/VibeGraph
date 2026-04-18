import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
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
                <span aria-hidden="true">📁</span> Upload Project
            </button>

            {isModalOpen && (
                <div className="upload-modal-overlay" onClick={() => !isAnalyzing && setIsModalOpen(false)}>
                    <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="upload-canvas-area p-8">
                            <span style={{ display: 'inline-flex', position: 'absolute', top: '16px', right: '16px', zIndex: 50 }} title={isAnalyzing ? "Cannot close while analyzing project" : "Close Upload Modal"}>
                                <button
                                    className="modal-close-btn"
                                    onClick={() => setIsModalOpen(false)}
                                    disabled={isAnalyzing}
                                    aria-label="Close Upload Modal"
                                ><span aria-hidden="true">✕</span></button>
                            </span>
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
                                            background: 'rgba(255, 255, 255, 0.05)',
                                            border: '1px dashed var(--outline-variant)',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            color: 'var(--text-primary)', fontSize: '16px', fontWeight: 600,
                                            zIndex: 10,
                                        }}>
                                            Drop files here
                                        </div>
                                    )}
                                    <div className="corner-accent top-left"></div>
                                    <div className="corner-accent top-right"></div>
                                    <div className="corner-accent bottom-left"></div>
                                    <div className="corner-accent bottom-right"></div>

                                    <div className="upload-content-wrapper">
                                        <div className="upload-icon-container">
                                            <span className="material-symbols-outlined upload-icon" aria-hidden="true" style={{ fontVariationSettings: "'wght' 200" }}>upload_file</span>
                                        </div>
                                        <div className="upload-text-container">
                                            <h2>INITIATE INGESTION</h2>
                                            <p className="upload-hint">DRAG ASSETS TO CANVAS OR BROWSE LOCAL DIRECTORY</p>
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
                                        <button className="upload-select-btn" tabIndex={-1} aria-hidden="true">SELECT FILES</button>
                                    </div>
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
