import React, { useMemo, useState } from 'react';

// PERFORMANCE OPTIMIZATION (Bolt): Zero-allocation string helpers
// Replaces O(N) array-creating string.split(/[/\\]/).pop() / slice() logic
// which causes massive garbage collection pressure when mapping over large node arrays.
const getShortName = (path) => {
    if (!path) return '';
    const lastSlash = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'));
    return lastSlash >= 0 ? path.substring(lastSlash + 1) : path;
};

const getDirName = (path) => {
    if (!path) return '';
    const lastSlash = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'));
    return lastSlash >= 0 ? path.substring(0, lastSlash) : '';
};

// Pluralize a node-type label for count summaries, e.g. "1 class" / "2 classes".
// Types ending in "s" (class, ...) take "es"; everything else takes "s".
const pluralizeType = (type, count) => {
    if (count === 1) return type;
    return /s$/.test(type) ? `${type}es` : `${type}s`;
};

const typeIcons = {
    function: '⚡',
    class: '🏗️',
    entry_point: '🚀',
    builtin: '🐍',
    external: '📦',
    imported_local: '🔗',
    module: '📁',
    unresolved: '?',
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
    collapsed,
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
            className={`file-sidebar${mobileOpen ? ' sidebar-open' : ''}${collapsed ? ' collapsed' : ''}`}
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
                            title="View all files"
                            aria-label={`All Files, ${totalNodeCount || 0} nodes total`}
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
                            const shortName = getShortName(file) || file;
                            const dirName = getDirName(file);

                            let typeStr = '';
                            if (stats.types) {
                                for (const type in stats.types) {
                                    const count = stats.types[type];
                                    if (typeStr) typeStr += ', ';
                                    typeStr += `${count} ${pluralizeType(type, count)}`;
                                }
                            }
                            const ariaLabel = `${file}, ${stats.count || 0} nodes${typeStr ? `. ${typeStr}` : ''}`;

                            return (
                                <button
                                    key={file}
                                    className={`sidebar-file ${isSelected ? 'selected' : ''}`}
                                    onClick={() => onSelectFile(file)}
                                    aria-current={isSelected ? 'true' : undefined}
                                    title={ariaLabel}
                                    aria-label={ariaLabel}
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
                                            {(() => {
                                                const typeBadges = [];
                                                for (const type in stats.types) {
                                                    const count = stats.types[type];
                                                    typeBadges.push(
                                                        <span key={type} className={`type-badge type-${type}`}>
                                                            <span aria-hidden="true">{typeIcons[type] || '○'}</span> {count}
                                                        </span>
                                                    );
                                                }
                                                return typeBadges;
                                            })()}
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

                    {deps && (() => {
                        let isEmpty = true;
                        for (const _ in deps) {
                            isEmpty = false;
                            break;
                        }
                        if (isEmpty) {
                            return <div className="deps-empty">No file dependencies found.</div>;
                        }

                        const depElements = [];
                        for (const file in deps) {
                            const info = deps[file];
                            const shortName = getShortName(file) || file;
                            const isSelected = file === selectedFile;
                            const imports = info.imports || info.imports_from || [];
                            const importedBy = info.imported_by || [];

                            depElements.push(
                                <div key={file} className={`deps-file ${isSelected ? 'selected' : ''}`}>
                                    <button
                                        className="deps-file-header"
                                        onClick={() => onSelectFile(file)}
                                        title={file}
                                        aria-label={file}
                                    >
                                        <span className="deps-file-icon" aria-hidden="true">📄</span>
                                        <span className="deps-file-name" title={file}>{shortName}</span>
                                    </button>

                                    {imports.length > 0 && (
                                        <div className="deps-section">
                                            <span className="deps-section-label">→ imports</span>
                                            {(() => {
                                                const impElements = [];
                                                for (let i = 0; i < imports.length; i++) {
                                                    const imp = imports[i];
                                                    const impName = typeof imp === 'string' ? imp : imp.module || imp.name;
                                                    const details = typeof imp === 'object' ? imp.names : null;
                                                    impElements.push(
                                                        <div key={i} className="deps-item">
                                                            <span className="deps-item-name" title={impName}>
                                                                {getShortName(impName || '')}
                                                            </span>
                                                            {details && details.length > 0 && (
                                                                <span className="deps-item-detail" title={details.join(', ')}>
                                                                    ({details.join(', ')})
                                                                </span>
                                                            )}
                                                        </div>
                                                    );
                                                }
                                                return impElements;
                                            })()}
                                        </div>
                                    )}

                                    {importedBy.length > 0 && (
                                        <div className="deps-section">
                                            <span className="deps-section-label">← used by</span>
                                            {(() => {
                                                const refElements = [];
                                                for (let i = 0; i < importedBy.length; i++) {
                                                    const ref = importedBy[i];
                                                    refElements.push(
                                                        <button
                                                            key={i}
                                                            className="deps-item deps-item-clickable"
                                                            onClick={() => onSelectFile(typeof ref === 'string' ? ref : ref.file)}
                                                            title={typeof ref === 'string' ? ref : ref.file}
                                                            aria-label={typeof ref === 'string' ? ref : ref.file}
                                                        >
                                                            <span className="deps-item-name" title={typeof ref === 'string' ? ref : ref.file}>
                                                                {getShortName(typeof ref === 'string' ? ref : ref.file || '')}
                                                            </span>
                                                        </button>
                                                    );
                                                }
                                                return refElements;
                                            })()}
                                        </div>
                                    )}
                                </div>
                            );
                        }
                        return depElements;
                    })()}
                </div>
            )}
        </div>
    );
};

// PERFORMANCE OPTIMIZATION (Bolt):
// Wrap FileSidebar in React.memo() to prevent O(N) re-renders
// of the entire file tree when the App's rapid simulation state changes.
export default React.memo(FileSidebar);
