import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('react-markdown', () => ({
  default: ({ children }) => <div data-testid="markdown">{children}</div>,
}));

vi.mock('../utils/sse', () => ({
  consumeSseChunk: vi.fn((buffer, chunk) => ({
    buffer: '',
    events: chunk.includes('[DONE]')
      ? ['[DONE]']
      : [chunk.replace('data: ', '').trim()],
  })),
}));

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
    allEdges: [],
    isOpen: true,
    onToggle: vi.fn(),
    apiKey: 'test-key',
    selectedModel: 'anthropic/claude-haiku-4.5',
    aiReady: true,
    onOpenAiSettings: vi.fn(),
  };
  return render(<ChatDrawer {...defaults} {...props} />);
}

describe('ChatDrawer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    globalThis.fetch = vi.fn();
    localStorage.clear();
  });

  it('renders FAB button when closed', () => {
    render(
      <ChatDrawer
        selectedNode={null}
        allNodes={[]}
        isOpen={false}
        onToggle={vi.fn()}
        apiKey="test-key"
        selectedModel="anthropic/claude-haiku-4.5"
        aiReady={true}
        onOpenAiSettings={vi.fn()}
      />
    );
    expect(screen.getByLabelText('Open Chat')).toBeInTheDocument();
  });

  it('uses inherited icon color for the FAB instead of a hardcoded white style', () => {
    render(
      <ChatDrawer
        selectedNode={null}
        allNodes={[]}
        isOpen={false}
        onToggle={vi.fn()}
        apiKey="test-key"
        selectedModel="anthropic/claude-haiku-4.5"
        aiReady={true}
        onOpenAiSettings={vi.fn()}
      />
    );

    const fabIcon = screen.getByLabelText('Open Chat').querySelector('svg');
    expect(fabIcon).toBeTruthy();
    expect(fabIcon?.getAttribute('style')).toBeNull();
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
        apiKey="test-key"
        selectedModel="anthropic/claude-haiku-4.5"
        aiReady={true}
        onOpenAiSettings={vi.fn()}
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

  it('shows node selection prompt when no node selected', () => {
    renderDrawer({ selectedNode: null });
    expect(screen.getByText(/Select a function or class on the graph/)).toBeInTheDocument();
    expect(screen.getByText('No node selected')).toBeInTheDocument();
    expect(screen.getByText(/Ctrl\+K/)).toBeInTheDocument();
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
    renderDrawer({ selectedNode: MOCK_NODE });
    expect(screen.getByRole('button', { name: 'Type a message to send' })).toBeDisabled();
  });

  it('send button is disabled when no node is selected', () => {
    renderDrawer({ selectedNode: null });
    expect(screen.getByRole('button', { name: 'Select a graph node to send' })).toBeDisabled();
  });

  it('send button stays disabled without a selected node even when input has text', async () => {
    const user = userEvent.setup();
    renderDrawer({ selectedNode: null });

    await user.type(
      screen.getByPlaceholderText('Select a node on the graph to ask…'),
      'hello'
    );
    expect(screen.getByRole('button', { name: 'Select a graph node to send' })).toBeDisabled();
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it('send button is enabled when input has text and a node is selected', async () => {
    const user = userEvent.setup();
    renderDrawer({ selectedNode: MOCK_NODE });

    await user.type(screen.getByPlaceholderText('Ask a question...'), 'hello');
    expect(screen.getByRole('button', { name: 'Send message' })).not.toBeDisabled();
  });

  it('shows a visible Enter shortcut hint without changing the send button name', async () => {
    const user = userEvent.setup();
    renderDrawer({ selectedNode: MOCK_NODE });

    await user.type(screen.getByPlaceholderText('Ask a question...'), 'hello');

    expect(screen.getByRole('button', { name: 'Send message' })).toBeInTheDocument();
    expect(screen.getByText('Enter')).toBeVisible();
  });

  it('adds chat input help text that explains Enter and Shift+Enter behavior', () => {
    renderDrawer({ selectedNode: MOCK_NODE });

    const input = screen.getByLabelText('Chat input');
    const helpId = input.getAttribute('aria-describedby');

    expect(helpId).toBeTruthy();
    expect(document.getElementById(helpId)).toHaveTextContent(
      'Press Enter to send. Press Shift+Enter to add a new line.'
    );
  });

  it('blocks API send without selected node and shows guidance', async () => {
    const user = userEvent.setup();
    renderDrawer({ selectedNode: null, allNodes: [MOCK_NODE] });

    const input = screen.getByPlaceholderText('Select a node on the graph to ask…');
    await user.type(input, 'What does this project do?{Enter}');

    expect(globalThis.fetch).not.toHaveBeenCalled();
    expect(screen.getByText('What does this project do?')).toBeInTheDocument();
    expect(
      screen.getByText(/Pick a function or class on the graph first/)
    ).toBeInTheDocument();
  });

  it('prompts for AI settings when key is missing', async () => {
    const user = userEvent.setup();
    const onOpenAiSettings = vi.fn();
    renderDrawer({
      selectedNode: MOCK_NODE,
      aiReady: false,
      apiKey: '',
      onOpenAiSettings,
    });

    await user.type(
      screen.getByPlaceholderText('Ask a question...'),
      'What is main?'
    );
    await user.click(screen.getByRole('button', { name: 'Send message' }));

    expect(onOpenAiSettings).toHaveBeenCalledTimes(1);
    expect(globalThis.fetch).not.toHaveBeenCalled();
    expect(
      screen.getByText(/Open AI Settings and add your OpenRouter key/i)
    ).toBeInTheDocument();
  });

  it('sends message and displays user message in chat', async () => {
    const user = userEvent.setup();
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('data: Hello world\n\n'));
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      },
    });
    globalThis.fetch.mockResolvedValue({ ok: true, body: stream });

    renderDrawer({
      selectedNode: MOCK_NODE,
      allNodes: [
        MOCK_NODE,
        { id: 'caller_fn', data: { type: 'function', file: 'app.py' } },
        { id: 'callee_fn', data: { type: 'function', file: 'app.py' } },
      ],
      allEdges: [
        { source: 'caller_fn', target: 'main' },
        { source: 'main', target: 'callee_fn' },
      ],
    });

    await user.type(
      screen.getByPlaceholderText('Ask a question...'),
      'What is main?'
    );
    await user.click(screen.getByRole('button', { name: 'Send message' }));

    expect(screen.getByText('What is main?')).toBeInTheDocument();
    const [, options] = globalThis.fetch.mock.calls[0];
    expect(JSON.parse(options.body)).toMatchObject({
      callers: ['caller_fn'],
      callees: ['callee_fn'],
      neighbors: ['caller_fn', 'callee_fn'],
    });
  });

  it('falls back to /api/chat when streaming fails', async () => {
    const user = userEvent.setup();
    globalThis.fetch
      .mockResolvedValueOnce({ ok: false, body: null })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ answer: 'Fallback answer' }),
      });

    renderDrawer({ selectedNode: MOCK_NODE });

    await user.type(
      screen.getByPlaceholderText('Ask a question...'),
      'test question'
    );
    await user.click(screen.getByRole('button', { name: 'Send message' }));

    await waitFor(() => {
      expect(screen.getByText('Fallback answer')).toBeInTheDocument();
    });
  });

  it('shows error message when both stream and fallback fail', async () => {
    const user = userEvent.setup();
    globalThis.fetch.mockRejectedValue(new Error('Network error'));

    renderDrawer({ selectedNode: MOCK_NODE });

    await user.type(screen.getByPlaceholderText('Ask a question...'), 'test');
    await user.click(screen.getByRole('button', { name: 'Send message' }));

    await waitFor(() => {
      expect(screen.getByText(/Could not reach the backend/)).toBeInTheDocument();
    });
  });

  it('sends message with Enter key', async () => {
    const user = userEvent.setup();
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      },
    });
    globalThis.fetch.mockResolvedValue({ ok: true, body: stream });

    renderDrawer({ selectedNode: MOCK_NODE });

    const input = screen.getByPlaceholderText('Ask a question...');
    await user.type(input, 'Enter key test{Enter}');

    expect(globalThis.fetch).toHaveBeenCalled();
  });

  it('does not send the message on Shift+Enter and keeps the newline in the input', async () => {
    const user = userEvent.setup();
    renderDrawer({ selectedNode: MOCK_NODE });

    const input = screen.getByPlaceholderText('Ask a question...');
    await user.type(input, 'Line 1{Shift>}{Enter}{/Shift}Line 2');

    expect(globalThis.fetch).not.toHaveBeenCalled();
    expect(input).toHaveValue('Line 1\nLine 2');
  });

  it('resets messages when selected node changes', async () => {
    const user = userEvent.setup();
    const encoder = new TextEncoder();
    globalThis.fetch.mockResolvedValue({
      ok: true,
      body: new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('data: [DONE]\n\n'));
          controller.close();
        },
      }),
    });

    const { rerender } = renderDrawer({ selectedNode: MOCK_NODE });

    await user.type(screen.getByPlaceholderText('Ask a question...'), 'hello{Enter}');
    await waitFor(() => expect(screen.getByText('hello')).toBeInTheDocument());

    rerender(
      <ChatDrawer
        selectedNode={{ id: 'helper', data: { label: 'helper', file: 'utils.py' } }}
        allNodes={[]}
        isOpen={true}
        onToggle={vi.fn()}
        apiKey="test-key"
        selectedModel="anthropic/claude-haiku-4.5"
        aiReady={true}
        onOpenAiSettings={vi.fn()}
      />
    );

    expect(screen.queryByText('hello')).not.toBeInTheDocument();
  });

  // Regression coverage for #436: the user's own message must stay in the
  // conversation alongside the assistant reply, in the correct order.
  it('keeps the user message and renders it before the AI reply', async () => {
    const user = userEvent.setup();
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('data: Because reasons\n\n'));
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      },
    });
    globalThis.fetch.mockResolvedValue({ ok: true, body: stream });

    renderDrawer({ selectedNode: MOCK_NODE });

    await user.type(screen.getByPlaceholderText('Ask a question...'), 'Why?');
    await user.click(screen.getByRole('button', { name: 'Send message' }));

    await waitFor(() =>
      expect(screen.getByText('Because reasons')).toBeInTheDocument()
    );

    const userMessage = screen.getByText('Why?');
    const aiMessage = screen.getByText('Because reasons');
    expect(userMessage).toBeInTheDocument();
    // DOCUMENT_POSITION_FOLLOWING (4) means userMessage comes before aiMessage.
    expect(
      userMessage.compareDocumentPosition(aiMessage) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
  });

  it('keeps the user message when the response is empty', async () => {
    const user = userEvent.setup();
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      },
    });
    globalThis.fetch.mockResolvedValue({ ok: true, body: stream });

    renderDrawer({ selectedNode: MOCK_NODE });

    await user.type(screen.getByPlaceholderText('Ask a question...'), 'Anyone there?');
    await user.click(screen.getByRole('button', { name: 'Send message' }));

    await waitFor(() =>
      expect(
        screen.queryByRole('button', { name: 'Waiting for AI response...' })
      ).not.toBeInTheDocument()
    );
    expect(screen.getByText('Anyone there?')).toBeInTheDocument();
  });

  it('keeps the user message visible when the request fails', async () => {
    const user = userEvent.setup();
    globalThis.fetch.mockRejectedValue(new Error('Network error'));

    renderDrawer({ selectedNode: MOCK_NODE });

    await user.type(screen.getByPlaceholderText('Ask a question...'), 'Still here?');
    await user.click(screen.getByRole('button', { name: 'Send message' }));

    await waitFor(() =>
      expect(screen.getByText(/Could not reach the backend/)).toBeInTheDocument()
    );
    expect(screen.getByText('Still here?')).toBeInTheDocument();
  });

  it('preserves visible history when the drawer is closed and reopened', async () => {
    const user = userEvent.setup();
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('data: Stored reply\n\n'));
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      },
    });
    globalThis.fetch.mockResolvedValue({ ok: true, body: stream });

    const { rerender } = renderDrawer({ selectedNode: MOCK_NODE });

    await user.type(screen.getByPlaceholderText('Ask a question...'), 'Remember me');
    await user.click(screen.getByRole('button', { name: 'Send message' }));
    await waitFor(() => expect(screen.getByText('Stored reply')).toBeInTheDocument());

    const baseProps = {
      selectedNode: MOCK_NODE,
      allNodes: [],
      allEdges: [],
      onToggle: vi.fn(),
      apiKey: 'test-key',
      selectedModel: 'anthropic/claude-haiku-4.5',
      aiReady: true,
      onOpenAiSettings: vi.fn(),
    };
    rerender(<ChatDrawer {...baseProps} isOpen={false} />);
    rerender(<ChatDrawer {...baseProps} isOpen={true} />);

    expect(screen.getByText('Remember me')).toBeInTheDocument();
    expect(screen.getByText('Stored reply')).toBeInTheDocument();
  });
});
