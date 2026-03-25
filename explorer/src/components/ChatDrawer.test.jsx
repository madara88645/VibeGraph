import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock react-markdown (avoids complex unified/remark dependencies in tests)
vi.mock('react-markdown', () => ({
    default: ({ children }) => <div data-testid="markdown">{children}</div>,
}));

// Mock SSE utility
vi.mock('../utils/sse', () => ({
    consumeSseChunk: vi.fn((buffer, chunk) => ({
        buffer: '',
        events: chunk.includes('[DONE]') ? ['[DONE]'] : [chunk.replace('data: ', '').trim()],
    })),
}));

// jsdom doesn't implement scrollIntoView
window.HTMLElement.prototype.scrollIntoView = vi.fn();

import ChatDrawer from './ChatDrawer';

const MOCK_NODE = {
    id: 'main',
    data: { label: 'main', type: 'function', file: 'app.py' },
};

function renderDrawer(props = {}) {
    const defaults = {
        selectedNode: null,
        allNodes: [],
        isOpen: true,
        onToggle: vi.fn(),
    };
    return render(<ChatDrawer {...defaults} {...props} />);
}

describe('ChatDrawer', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        global.fetch = vi.fn();
    });

    it('renders FAB button when closed', () => {
        render(
            <ChatDrawer
                selectedNode={null}
                allNodes={[]}
                isOpen={false}
                onToggle={vi.fn()}
            />
        );
        expect(screen.getByLabelText('Open Chat')).toBeInTheDocument();
    });

    it('calls onToggle when FAB is clicked', async () => {
        const user = userEvent.setup();
        const onToggle = vi.fn();
        render(
            <ChatDrawer
                selectedNode={null}
                allNodes={[]}
                isOpen={false}
                onToggle={onToggle}
            />
        );
        await user.click(screen.getByLabelText('Open Chat'));
        expect(onToggle).toHaveBeenCalled();
    });

    it('renders chat header when open', () => {
        renderDrawer();
        expect(screen.getByText('Vibe Chat')).toBeInTheDocument();
    });

    it('shows context badge for selected node', () => {
        renderDrawer({ selectedNode: MOCK_NODE });
        expect(screen.getByText(/Asking about/)).toBeInTheDocument();
        expect(screen.getByText('main')).toBeInTheDocument();
    });

    it('shows general project prompt when no node selected', () => {
        renderDrawer({ selectedNode: null });
        expect(screen.getByText(/Ask a general question/)).toBeInTheDocument();
    });

    it('shows node-specific prompt when node is selected', () => {
        renderDrawer({ selectedNode: MOCK_NODE });
        expect(screen.getByText(/Ask anything about "main"/)).toBeInTheDocument();
    });

    it('closes drawer when close button is clicked', async () => {
        const user = userEvent.setup();
        const onToggle = vi.fn();
        renderDrawer({ onToggle });

        await user.click(screen.getByLabelText('Close Chat'));
        expect(onToggle).toHaveBeenCalled();
    });

    it('send button is disabled when input is empty', () => {
        renderDrawer();
        expect(screen.getByLabelText('Send message')).toBeDisabled();
    });

    it('send button is enabled when input has text', async () => {
        const user = userEvent.setup();
        renderDrawer();

        await user.type(screen.getByPlaceholderText('Ask a question…'), 'hello');
        expect(screen.getByLabelText('Send message')).not.toBeDisabled();
    });

    it('sends message and displays user message in chat', async () => {
        const user = userEvent.setup();
        // Simulate a successful SSE response
        const encoder = new TextEncoder();
        const stream = new ReadableStream({
            start(controller) {
                controller.enqueue(encoder.encode('data: Hello world\n\n'));
                controller.enqueue(encoder.encode('data: [DONE]\n\n'));
                controller.close();
            },
        });
        global.fetch.mockResolvedValue({ ok: true, body: stream });

        renderDrawer({ selectedNode: MOCK_NODE });

        await user.type(screen.getByPlaceholderText('Ask a question…'), 'What is main?');
        await user.click(screen.getByLabelText('Send message'));

        // User message appears immediately
        expect(screen.getByText('What is main?')).toBeInTheDocument();
    });

    it('falls back to /api/chat when streaming fails', async () => {
        const user = userEvent.setup();
        // First call (stream) fails
        global.fetch
            .mockResolvedValueOnce({ ok: false, body: null })
            .mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ answer: 'Fallback answer' }),
            });

        renderDrawer({ selectedNode: MOCK_NODE });

        await user.type(screen.getByPlaceholderText('Ask a question…'), 'test question');
        await user.click(screen.getByLabelText('Send message'));

        await waitFor(() => {
            expect(screen.getByText('Fallback answer')).toBeInTheDocument();
        });
    });

    it('shows error message when both stream and fallback fail', async () => {
        const user = userEvent.setup();
        global.fetch.mockRejectedValue(new Error('Network error'));

        renderDrawer({ selectedNode: MOCK_NODE });

        await user.type(screen.getByPlaceholderText('Ask a question…'), 'test');
        await user.click(screen.getByLabelText('Send message'));

        await waitFor(() => {
            expect(screen.getByText(/Could not reach the backend/)).toBeInTheDocument();
        });
    });

    it('sends message with Enter key (not Shift+Enter)', async () => {
        const user = userEvent.setup();
        const encoder = new TextEncoder();
        const stream = new ReadableStream({
            start(controller) {
                controller.enqueue(encoder.encode('data: [DONE]\n\n'));
                controller.close();
            },
        });
        global.fetch.mockResolvedValue({ ok: true, body: stream });

        renderDrawer({ selectedNode: MOCK_NODE });

        const input = screen.getByPlaceholderText('Ask a question…');
        await user.type(input, 'Enter key test{Enter}');

        expect(global.fetch).toHaveBeenCalled();
    });

    it('resets messages when selected node changes', async () => {
        const user = userEvent.setup();
        const encoder = new TextEncoder();
        global.fetch.mockResolvedValue({
            ok: true,
            body: new ReadableStream({
                start(controller) {
                    controller.enqueue(encoder.encode('data: [DONE]\n\n'));
                    controller.close();
                },
            }),
        });

        const { rerender } = renderDrawer({ selectedNode: MOCK_NODE });

        await user.type(screen.getByPlaceholderText('Ask a question…'), 'hello{Enter}');
        await waitFor(() => expect(screen.getByText('hello')).toBeInTheDocument());

        // Switch to a different node
        rerender(
            <ChatDrawer
                selectedNode={{ id: 'helper', data: { label: 'helper', file: 'utils.py' } }}
                allNodes={[]}
                isOpen={true}
                onToggle={vi.fn()}
            />
        );

        // Messages should be cleared
        expect(screen.queryByText('hello')).not.toBeInTheDocument();
    });
});
