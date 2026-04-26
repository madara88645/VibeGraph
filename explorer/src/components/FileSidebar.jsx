import React, { useMemo, useState } from 'react';

const typeIcons = {
    function: '⚡',
    class: '🏗️',
    entry_point: '🚀',
    default: '○',
};

const FileSidebar = ({
    files,
    selectedFile,
    onSelectFile,
    nodeStats,
    totalNodeCount,
    mobileOpen,
    fileDependencies,
}) => {
    const [activeTab, setActiveTab] = useState('files');
    const deps = useMemo(() => {
        if (!Array.isArray(fileDependencies) || fileDependencies.length === 0) {
            return null;
        }

        const grouped = {};
        fileDependencies.forEach((dependency) => {
            const sourceFile = dependency.source_file || 'unknown';
            if (!grouped[sourceFile]) {
                grouped[sourceFile] = {
                    imports: [],
                    imports_from: [],
                    imported_by: [],
                };
            }

            grouped[sourceFile].imports.push({
                module: dependency.target_file,
                names: dependency.imports || [],
            });
        });

        return grouped;
    }, [fileDependencies]);

    return (
        <div
            id="file-sidebar-panel"
            className={`file-sidebar${mobileOpen ? ' sidebar-open' : ''}`}
        >
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
                    <span aria-hidden="true">📁</span> Files
                </button>
                <button
                    id="tab-deps"
                    role="tab"
                    aria-selected={activeTab === 'deps'}
                    aria-controls="panel-deps"
                    className={`sidebar-tab ${activeTab === 'deps' ? 'active' : ''}`}
                    onClick={() => setActiveTab('deps')}
                >
                    <span aria-hidden="true">🔗</span> Deps
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
                            aria-current={!selectedFile ? 'true' : undefined}
                            aria-label="View all files"
                            title="All Files"
                        >
                            <div className="file-main">
                                <span className="file-icon" aria-hidden="true">🗂️</span>
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
                                    aria-current={isSelected ? 'true' : undefined}
                                    aria-label={`View file ${file}`}
                                >
                                    <div className="file-main">
                                        <span className="file-icon" aria-hidden="true">{stats.hasEntry ? '🚀' : '📄'}</span>
                                        <span className="file-name" title={file}>{shortName}</span>
                                        <span className="file-count">{stats.count || 0}</span>
                                    </div>
                                    {dirName && (
                                        <div className="file-dir" title={dirName}>{dirName}</div>
                                    )}
                                    {isSelected && stats.types && (
                                        <div className="file-types">
                                            {Object.entries(stats.types).map(([type, count]) => (
                                                <span key={type} className={`type-badge type-${type}`}>
                                                    <span aria-hidden="true">{typeIcons[type] || '○'}</span> {count}
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
                            Dependency view appears after you upload and analyze a project.
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
                                    aria-label={`View dependencies for ${file}`}
                                    title={file}
                                >
                                    <span className="deps-file-icon" aria-hidden="true">📄</span>
                                    <span className="deps-file-name" title={file}>{shortName}</span>
                                </button>

                                {imports.length > 0 && (
                                    <div className="deps-section">
                                        <span className="deps-section-label">→ imports</span>
                                        {imports.map((imp, i) => {
                                            const impName = typeof imp === 'string' ? imp : imp.module || imp.name;
                                            const details = typeof imp === 'object' ? imp.names : null;
                                            return (
                                                <div key={i} className="deps-item">
                                                    <span className="deps-item-name" title={impName}>
                                                        {(impName || '').split(/[/\\]/).pop()}
                                                    </span>
                                                    {details && details.length > 0 && (
                                                        <span className="deps-item-detail" title={details.join(', ')}>
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
                                        {importedBy.map((ref, i) => {
                                            const refPath = typeof ref === 'string' ? ref : ref.file;
                                            return (
                                                <button
                                                    key={i}
                                                    className="deps-item deps-item-clickable"
                                                    onClick={() => onSelectFile(refPath)}
                                                    aria-label={`View file ${refPath}`}
                                                    title={refPath}
                                                >
                                                    <span className="deps-item-name" title={refPath}>
                                                        {(refPath || '').split(/[/\\]/).pop()}
                                                    </span>
                                                </button>
                                            );
                                        })}
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
