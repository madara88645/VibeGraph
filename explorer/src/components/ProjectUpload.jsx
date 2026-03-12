import React, { useState, useRef } from 'react';

const ProjectUpload = ({ onUploadSuccess }) => {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const fileInputRef = useRef(null);

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
            } else {
                console.error("Analysis success but invalid graph data returned", result);
                alert("Analysis completed but graph data is missing. Check backend logs.");
            }
        } catch (error) {
            console.error("Project upload failed:", error);
            alert(`Error: ${error.message}`);
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
            >
                📁 Upload Project
            </button>

            {isModalOpen && (
                <div className="upload-modal-overlay" onClick={() => !isAnalyzing && setIsModalOpen(false)}>
                    <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="upload-modal-header">
                            <h3>Upload Project</h3>
                            <button
                                className="modal-close-btn"
                                onClick={() => setIsModalOpen(false)}
                                disabled={isAnalyzing}
                                aria-label="Close Upload Modal"
                            >✕</button>
                        </div>

                        <div className="upload-modal-body">
                            {isAnalyzing ? (
                                <div className="analyzing-state">
                                    <div className="vibe-spinner"></div>
                                    <p>Analyzing Project...</p>
                                    <span className="analyzing-subtitle">Building call graph, mapping vibes</span>
                                </div>
                            ) : (
                                <div className="upload-zone" onClick={() => fileInputRef.current?.click()}>
                                    <div className="upload-icon">📤</div>
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
                                    <button className="upload-select-btn">Select Folder</button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProjectUpload;
