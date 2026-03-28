import React, { useState, useEffect } from 'react';

const typeIcons = {
    function: '⚡',
    class: '🏗️',
    entry_point: '🚀',
    default: '○',
};

const FileSidebar = ({ files, selectedFile, onSelectFile, nodeStats, totalNodeCount, mobileOpen }) => {
    const [activeTab, setActiveTab] = useState('files');
    const [deps, setDeps] = useState(null);

    // Load file_dependencies from graph_data.json
    useEffect(() => {
        const loadDeps = async () => {
            try {
                const res = await fetch('/graph_data.json');
                if (!res.ok) return;
                const data = await res.json();
                setDeps(data.file_dependencies || null);
            } catch {
                // silently fail
            }
        };
        loadDeps();
    }, []);

    return (
        <div className={`file-sidebar${mobileOpen ? ' sidebar-open' : ''}`}>
            {/* Tabs */}
            <div className="sidebar-tabs" role="tablist" aria-label="Sidebar views">
                <button
                    id="tab-files"
                    role="tab"
                    aria-selected={activeTab === 'files'}
                    aria-controls="panel-files"
                    className={`sidebar-tab ${activeTab === 'files' ? 'active' : ''}`}
                    onClick={() => setActiveTab('files')}
                >
                    📁 Files
                </button>
                <button
                    id="tab-deps"
                    role="tab"
                    aria-selected={activeTab === 'deps'}
                    aria-controls="panel-deps"
                    className={`sidebar-tab ${activeTab === 'deps' ? 'active' : ''}`}
                    onClick={() => setActiveTab('deps')}
                >
                    🔗 Deps
                </button>
            </div>

            {/* Files Tab */}
            {activeTab === 'files' && (
                <div
                    id="panel-files"
                    role="tabpanel"
                    aria-labelledby="tab-files"
                    style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}
                >
                    <div className="sidebar-content">
                        <button
                            className={`sidebar-file all-files-btn ${!selectedFile ? 'selected' : ''}`}
                            onClick={() => onSelectFile(null)}
                        >
                            <div className="file-main">
                                <span className="file-icon">🗂️</span>
                                <span className="file-name">All Files</span>
                                <span className="file-count">{totalNodeCount || 0}</span>
                            </div>
                        </button>
                        {files.map(file => {
                            const stats = nodeStats[file] || {};
                            const isSelected = file === selectedFile;
                            const shortName = file.split(/[/\\]/).pop() || file;
                            const dirName = file.split(/[/\\]/).slice(0, -1).join('/');

                            return (
                                <button
                                    key={file}
                                    className={`sidebar-file ${isSelected ? 'selected' : ''}`}
                                    onClick={() => onSelectFile(file)}
                                >
                                    <div className="file-main">
                                        <span className="file-icon">{stats.hasEntry ? '🚀' : '📄'}</span>
                                        <span className="file-name">{shortName}</span>
                                        <span className="file-count">{stats.count || 0}</span>
                                    </div>
                                    {dirName && (
                                        <div className="file-dir">{dirName}</div>
                                    )}
                                    {isSelected && stats.types && (
                                        <div className="file-types">
                                            {Object.entries(stats.types).map(([type, count]) => (
                                                <span key={type} className={`type-badge type-${type}`}>
                                                    {typeIcons[type] || '○'} {count}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </button>
                            );
                        })}
                    </div>

                    {/* Legend */}
                    <div className="sidebar-legend">
                        <span>⚡ fn</span>
                        <span>🏗️ cls</span>
                        <span>🚀 entry</span>
                        <span>○ ref</span>
                    </div>
                </div>
            )}

            {/* Dependencies Tab */}
            {activeTab === 'deps' && (
                <div
                    className="sidebar-content"
                    id="panel-deps"
                    role="tabpanel"
                    aria-labelledby="tab-deps"
                >
                    {!deps && (
                        <div className="deps-empty">
                            No dependency data. Run analysis with <code>--deps</code> flag.
                        </div>
                    )}

                    {deps && Object.keys(deps).length === 0 && (
                        <div className="deps-empty">No file dependencies found.</div>
                    )}

                    {deps && Object.entries(deps).map(([file, info]) => {
                        const shortName = file.split(/[/\\]/).pop() || file;
                        const isSelected = file === selectedFile;
                        const imports = info.imports || info.imports_from || [];
                        const importedBy = info.imported_by || [];

                        return (
                            <div key={file} className={`deps-file ${isSelected ? 'selected' : ''}`}>
                                <button
                                    className="deps-file-header"
                                    onClick={() => onSelectFile(file)}
                                >
                                    <span className="deps-file-icon">📄</span>
                                    <span className="deps-file-name">{shortName}</span>
                                </button>

                                {imports.length > 0 && (
                                    <div className="deps-section">
                                        <span className="deps-section-label">→ imports</span>
                                        {imports.map((imp, i) => {
                                            const impName = typeof imp === 'string' ? imp : imp.module || imp.name;
                                            const details = typeof imp === 'object' ? imp.names : null;
                                            return (
                                                <div key={i} className="deps-item">
                                                    <span className="deps-item-name">
                                                        {(impName || '').split(/[/\\]/).pop()}
                                                    </span>
                                                    {details && details.length > 0 && (
                                                        <span className="deps-item-detail">
                                                            ({details.join(', ')})
                                                        </span>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}

                                {importedBy.length > 0 && (
                                    <div className="deps-section">
                                        <span className="deps-section-label">← used by</span>
                                        {importedBy.map((ref, i) => (
                                            <button
                                                key={i}
                                                className="deps-item deps-item-clickable"
                                                onClick={() => onSelectFile(typeof ref === 'string' ? ref : ref.file)}
                                            >
                                                <span className="deps-item-name">
                                                    {(typeof ref === 'string' ? ref : ref.file || '').split(/[/\\]/).pop()}
                                                </span>
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

// PERFORMANCE OPTIMIZATION (Bolt):
// Wrap FileSidebar in React.memo() to prevent O(N) re-renders
// of the entire file tree when the App's rapid simulation state changes.
export default React.memo(FileSidebar);
