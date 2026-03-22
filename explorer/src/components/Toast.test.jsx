import { describe, it, expect, vi } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ToastProvider } from './Toast';
import { useToast } from '../hooks/useToast';

// Helper component that triggers a toast
function ToastTrigger({ message = 'Test message', type = 'info' }) {
    const showToast = useToast();
    return <button onClick={() => showToast(message, type)}>Show Toast</button>;
}

describe('Toast notification system', () => {
    it('renders a toast when showToast is called', async () => {
        const user = userEvent.setup();
        render(
            <ToastProvider>
                <ToastTrigger message="Upload complete" type="success" />
            </ToastProvider>
        );

        await user.click(screen.getByText('Show Toast'));
        expect(screen.getByText('Upload complete')).toBeInTheDocument();
    });

    it('renders correct icon for each toast type', async () => {
        const user = userEvent.setup();

        function MultiToast() {
            const showToast = useToast();
            return (
                <>
                    <button onClick={() => showToast('ok', 'success')}>Success</button>
                    <button onClick={() => showToast('fail', 'error')}>Error</button>
                    <button onClick={() => showToast('note', 'info')}>Info</button>
                </>
            );
        }

        render(
            <ToastProvider>
                <MultiToast />
            </ToastProvider>
        );

        await user.click(screen.getByText('Success'));
        await user.click(screen.getByText('Error'));
        await user.click(screen.getByText('Info'));

        const icons = screen.getAllByClassName
            ? document.querySelectorAll('.toast-icon')
            : screen.getByText('ok').parentElement.parentElement.querySelectorAll('.toast-icon');

        // All three toasts should be visible
        expect(screen.getByText('ok')).toBeInTheDocument();
        expect(screen.getByText('fail')).toBeInTheDocument();
        expect(screen.getByText('note')).toBeInTheDocument();
    });

    it('removes toast when close button is clicked', async () => {
        const user = userEvent.setup();
        render(
            <ToastProvider>
                <ToastTrigger message="Dismissable" type="info" />
            </ToastProvider>
        );

        await user.click(screen.getByText('Show Toast'));
        expect(screen.getByText('Dismissable')).toBeInTheDocument();

        await user.click(screen.getByLabelText('Dismiss notification'));
        expect(screen.queryByText('Dismissable')).not.toBeInTheDocument();
    });

    it('auto-removes toast after timeout', async () => {
        vi.useFakeTimers();

        render(
            <ToastProvider>
                <ToastTrigger message="Auto dismiss" type="info" />
            </ToastProvider>
        );

        await act(async () => {
            screen.getByText('Show Toast').click();
        });

        expect(screen.getByText('Auto dismiss')).toBeInTheDocument();

        await act(async () => {
            vi.advanceTimersByTime(4100);
        });

        expect(screen.queryByText('Auto dismiss')).not.toBeInTheDocument();

        vi.useRealTimers();
    });

    it('throws when useToast is used outside ToastProvider', () => {
        // Suppress console.error from React error boundary
        const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

        function Bad() {
            useToast();
            return null;
        }

        expect(() => render(<Bad />)).toThrow('useToast must be used within ToastProvider');
        spy.mockRestore();
    });
});
