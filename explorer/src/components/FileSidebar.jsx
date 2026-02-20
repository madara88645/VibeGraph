import React from 'react';

const typeIcons = {
    function: '⚡',
    class: '🏗️',
    entry_point: '🚀',
    default: '○',
};

const FileSidebar = ({ files, selectedFile, onSelectFile, nodeStats }) => {
    return (
        <div className="file-sidebar">
            <div className="sidebar-header">
                <span className="sidebar-icon">📁</span>
                <span>Explorer</span>
            </div>

            <div className="sidebar-content">
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
    );
};

export default FileSidebar;
