import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import React from 'react';
import ProjectUpload from './ProjectUpload';
import { ToastContext } from '../hooks/useToast';

// Wrap with ToastProvider context so useToast works
function renderWithToast(ui, { showToast = vi.fn() } = {}) {
    return render(
        <ToastContext.Provider value={showToast}>
            {ui}
        </ToastContext.Provider>
    );
}

describe('ProjectUpload', () => {
    let showToast;

    beforeEach(() => {
        showToast = vi.fn();
        globalThis.fetch = vi.fn();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('renders the upload button', () => {
        renderWithToast(<ProjectUpload onUploadSuccess={vi.fn()} />, { showToast });
        expect(screen.getByRole('button', { name: /upload new project/i })).toBeInTheDocument();
        expect(screen.getByText(/Upload Project/)).toBeInTheDocument();
    });

    it('opens modal when button is clicked', async () => {
        renderWithToast(<ProjectUpload onUploadSuccess={vi.fn()} />, { showToast });

        // Modal should not be visible initially
        expect(screen.queryByText('Upload your project')).not.toBeInTheDocument();

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        // Modal should now be visible
        expect(screen.getByText('Upload your project')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /close upload modal/i })).toBeInTheDocument();
    });

    it('closes modal when close button is clicked', async () => {
        renderWithToast(<ProjectUpload onUploadSuccess={vi.fn()} />, { showToast });

        // Open modal
        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });
        expect(screen.getByText('Upload your project')).toBeInTheDocument();

        // Close modal
        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /close upload modal/i }));
        });
        expect(screen.queryByText('Upload your project')).not.toBeInTheDocument();
    });

    it('closes modal when overlay is clicked', async () => {
        renderWithToast(<ProjectUpload onUploadSuccess={vi.fn()} />, { showToast });

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });
        expect(screen.getByText('Upload your project')).toBeInTheDocument();

        // Click the overlay
        await act(async () => {
            fireEvent.click(document.querySelector('.upload-modal-overlay'));
        });
        expect(screen.queryByText('Upload your project')).not.toBeInTheDocument();
    });

    it('closes modal on Escape key', async () => {
        renderWithToast(<ProjectUpload onUploadSuccess={vi.fn()} />, { showToast });

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });
        expect(screen.getByText('Upload your project')).toBeInTheDocument();

        await act(async () => {
            fireEvent.keyDown(window, { key: 'Escape' });
        });
        expect(screen.queryByText('Upload your project')).not.toBeInTheDocument();
    });

    it('shows loading state during upload', async () => {
        // fetch that never resolves to keep the loading state visible
        globalThis.fetch = vi.fn(() => new Promise(() => {}));

        renderWithToast(<ProjectUpload onUploadSuccess={vi.fn()} />, { showToast });

        // Open modal
        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        // Simulate file input change
        const fileInput = document.querySelector('input[type="file"]');
        const file = new File(['content'], 'main.py', { type: 'text/plain' });
        Object.defineProperty(file, 'webkitRelativePath', { value: 'project/main.py' });

        await act(async () => {
            fireEvent.change(fileInput, { target: { files: [file] } });
        });

        // Should show the analyzing state
        expect(screen.getByText('Analyzing project…')).toBeInTheDocument();
        // Close button should be disabled
        expect(screen.getByRole('button', { name: /Cannot close while analyzing project/i })).toBeDisabled();
    });

    it('handles successful upload with valid graph data', async () => {
        const mockResult = { nodes: [{ id: '1' }], edges: [{ source: '1', target: '2' }] };
        globalThis.fetch = vi.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve(mockResult),
            })
        );

        const onUploadSuccess = vi.fn();
        renderWithToast(<ProjectUpload onUploadSuccess={onUploadSuccess} />, { showToast });

        // Open modal
        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        const fileInput = document.querySelector('input[type="file"]');
        const file = new File(['content'], 'main.py', { type: 'text/plain' });

        await act(async () => {
            fireEvent.change(fileInput, { target: { files: [file] } });
        });

        expect(onUploadSuccess).toHaveBeenCalledWith(mockResult);
        expect(showToast).toHaveBeenCalledWith('Project analyzed successfully!', 'success');
    });

    it('blocks oversized file picker uploads before calling fetch', async () => {
        renderWithToast(<ProjectUpload onUploadSuccess={vi.fn()} />, { showToast });

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        const fileInput = document.querySelector('input[type="file"]');
        const file = new File(['content'], 'large.py', { type: 'text/plain' });
        Object.defineProperty(file, 'size', { value: 25 * 1024 * 1024 + 1 });

        await act(async () => {
            fireEvent.change(fileInput, { target: { files: [file] } });
        });

        expect(globalThis.fetch).not.toHaveBeenCalled();
        expect(showToast).toHaveBeenCalledWith(
            'Upload failed: Upload too large. Max total upload size is 25 MB.',
            'error'
        );
    });

    it('handles upload errors gracefully', async () => {
        globalThis.fetch = vi.fn(() =>
            Promise.resolve({
                ok: false,
                status: 500,
                statusText: 'Internal Server Error',
                json: () => Promise.resolve({ detail: 'Upload/Analysis failed due to an internal error.' }),
            })
        );

        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        renderWithToast(<ProjectUpload onUploadSuccess={vi.fn()} />, { showToast });

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        const fileInput = document.querySelector('input[type="file"]');
        const file = new File(['content'], 'main.py', { type: 'text/plain' });

        await act(async () => {
            fireEvent.change(fileInput, { target: { files: [file] } });
        });

        expect(showToast).toHaveBeenCalledWith(
            'Upload failed: Upload/Analysis failed due to an internal error.',
            'error'
        );
        consoleSpy.mockRestore();
    });

    it('handles network errors gracefully', async () => {
        globalThis.fetch = vi.fn(() => Promise.reject(new TypeError('Failed to fetch')));

        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        renderWithToast(<ProjectUpload onUploadSuccess={vi.fn()} />, { showToast });

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        const fileInput = document.querySelector('input[type="file"]');
        const file = new File(['content'], 'main.py', { type: 'text/plain' });

        await act(async () => {
            fireEvent.change(fileInput, { target: { files: [file] } });
        });

        expect(showToast).toHaveBeenCalledWith(
            'Upload failed: Backend is not reachable. Start the backend or check deployment.',
            'error'
        );
        consoleSpy.mockRestore();
    });

    it('does not treat an empty graph response as a successful upload', async () => {
        globalThis.fetch = vi.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ nodes: [], edges: [] }),
            })
        );

        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        const onUploadSuccess = vi.fn();
        renderWithToast(<ProjectUpload onUploadSuccess={onUploadSuccess} />, { showToast });

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        const fileInput = document.querySelector('input[type="file"]');
        const file = new File(['content'], 'main.py', { type: 'text/plain' });

        await act(async () => {
            fireEvent.change(fileInput, { target: { files: [file] } });
        });

        expect(onUploadSuccess).not.toHaveBeenCalled();
        expect(showToast).toHaveBeenCalledWith(
            'Upload failed: No analyzable code found. Try a Python, JavaScript, or TypeScript project.',
            'error'
        );
        expect(screen.getByText('Upload your project')).toBeInTheDocument();
        consoleSpy.mockRestore();
    });

    it('validates dropped files through the same upload path', async () => {
        globalThis.fetch = vi.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ nodes: [], edges: [] }),
            })
        );

        const onUploadSuccess = vi.fn();
        renderWithToast(<ProjectUpload onUploadSuccess={onUploadSuccess} />, { showToast });

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        const uploadZone = screen.getByRole('button', { name: /select a project folder/i });
        const file = new File(['content'], 'main.py', { type: 'text/plain' });

        await act(async () => {
            fireEvent.drop(uploadZone, {
                dataTransfer: {
                    files: [file],
                },
            });
        });

        expect(onUploadSuccess).not.toHaveBeenCalled();
        expect(showToast).toHaveBeenCalledWith(
            'Upload failed: No analyzable code found. Try a Python, JavaScript, or TypeScript project.',
            'error'
        );
    });

    it('does not close modal while analyzing when overlay is clicked', async () => {
        globalThis.fetch = vi.fn(() => new Promise(() => {}));

        renderWithToast(<ProjectUpload onUploadSuccess={vi.fn()} />, { showToast });

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        const fileInput = document.querySelector('input[type="file"]');
        const file = new File(['content'], 'main.py', { type: 'text/plain' });

        await act(async () => {
            fireEvent.change(fileInput, { target: { files: [file] } });
        });

        // Try clicking overlay while analyzing
        await act(async () => {
            fireEvent.click(document.querySelector('.upload-modal-overlay'));
        });

        // Modal should still be open (analyzing state prevents close)
        expect(screen.getByText('Analyzing project…')).toBeInTheDocument();
    });

    it('handles dropped ZIP files successfully', async () => {
        const mockResult = { nodes: [{ id: '1' }], edges: [{ source: '1', target: '2' }] };
        globalThis.fetch = vi.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve(mockResult),
            })
        );

        const onUploadSuccess = vi.fn();
        renderWithToast(<ProjectUpload onUploadSuccess={onUploadSuccess} />, { showToast });

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        const uploadZone = screen.getByRole('button', { name: /select a project folder/i });
        const file = new File(['zip content'], 'project.zip', { type: 'application/zip' });

        const mockEntry = {
            name: 'project.zip',
            isDirectory: false,
        };

        await act(async () => {
            fireEvent.drop(uploadZone, {
                dataTransfer: {
                    items: [
                        {
                            webkitGetAsEntry: () => mockEntry,
                        },
                    ],
                    files: [file],
                },
            });
        });

        expect(onUploadSuccess).toHaveBeenCalledWith(mockResult);
        expect(showToast).toHaveBeenCalledWith('Project analyzed successfully!', 'success');
    });

    it('blocks oversized drag-and-drop uploads before calling fetch', async () => {
        renderWithToast(<ProjectUpload onUploadSuccess={vi.fn()} />, { showToast });

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        const uploadZone = screen.getByRole('button', { name: /select a project folder/i });
        const file = new File(['zip content'], 'project.zip', { type: 'application/zip' });
        Object.defineProperty(file, 'size', { value: 25 * 1024 * 1024 + 1 });

        const mockEntry = {
            name: 'project.zip',
            isDirectory: false,
        };

        await act(async () => {
            fireEvent.drop(uploadZone, {
                dataTransfer: {
                    items: [
                        {
                            webkitGetAsEntry: () => mockEntry,
                        },
                    ],
                    files: [file],
                },
            });
        });

        expect(globalThis.fetch).not.toHaveBeenCalled();
        expect(showToast).toHaveBeenCalledWith(
            'Upload failed: Upload too large. Max total upload size is 25 MB.',
            'error'
        );
    });

    it('shows an info toast when upload succeeds with warnings', async () => {
        const mockResult = {
            nodes: [{ id: '1' }],
            edges: [{ source: '1', target: '2' }],
            warnings: ['huge.py skipped', 'bad.py skipped'],
        };
        globalThis.fetch = vi.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve(mockResult),
            })
        );

        const onUploadSuccess = vi.fn();
        renderWithToast(<ProjectUpload onUploadSuccess={onUploadSuccess} />, { showToast });

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        const fileInput = document.querySelector('input[type="file"]');
        const file = new File(['content'], 'main.py', { type: 'text/plain' });

        await act(async () => {
            fireEvent.change(fileInput, { target: { files: [file] } });
        });

        expect(onUploadSuccess).toHaveBeenCalledWith(mockResult);
        expect(showToast).toHaveBeenCalledWith(
            'Project analyzed with warnings: huge.py skipped (+1 more skipped files)',
            'info'
        );
        expect(showToast).toHaveBeenCalledWith('Project analyzed successfully!', 'success');
    });

    it('routes the modal demo CTA through onLoadDemo and keeps modal open to show loading', async () => {
        const onLoadDemo = vi.fn();
        const onUploadSuccess = vi.fn();
        const { rerender } = renderWithToast(
            <ProjectUpload onUploadSuccess={onUploadSuccess} onLoadDemo={onLoadDemo} isDemoLoading={false} />,
            { showToast }
        );

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        const demoBtn = screen.getByRole('button', { name: /try with a demo project/i });

        await act(async () => {
            fireEvent.click(demoBtn);
        });

        // The modal demo button now defers to App's handleLoadDemo (which loads the
        // graph AND pre-baked AI content), instead of loading only the graph itself.
        expect(onLoadDemo).toHaveBeenCalledTimes(1);
        expect(globalThis.fetch).not.toHaveBeenCalled();
        expect(onUploadSuccess).not.toHaveBeenCalled();

        // Modal should remain open to show loading state (which would be activated by App.jsx setting isDemoLoading=true)
        expect(screen.getByText('Upload your project')).toBeInTheDocument();

        // Simulate App.jsx transitioning isDemoLoading to true then back to false when done
        rerender(
            <ToastContext.Provider value={showToast}>
                <ProjectUpload onUploadSuccess={onUploadSuccess} onLoadDemo={onLoadDemo} isDemoLoading={true} />
            </ToastContext.Provider>
        );
        rerender(
            <ToastContext.Provider value={showToast}>
                <ProjectUpload onUploadSuccess={onUploadSuccess} onLoadDemo={onLoadDemo} isDemoLoading={false} />
            </ToastContext.Provider>
        );

        // Now the modal should be closed
        expect(screen.queryByText('Upload your project')).not.toBeInTheDocument();
    });

    it('disables the demo CTA button and shows loading state when isDemoLoading is true', async () => {
        renderWithToast(
            <ProjectUpload onUploadSuccess={vi.fn()} isDemoLoading={true} />,
            { showToast }
        );

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /upload new project/i }));
        });

        const demoBtn = screen.getByRole('button', { name: /loading demo/i });
        expect(demoBtn).toBeInTheDocument();
        expect(demoBtn).toBeDisabled();
    });
});
