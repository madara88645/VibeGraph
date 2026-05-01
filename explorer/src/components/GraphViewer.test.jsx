import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import GraphViewer from './GraphViewer';

vi.mock('reactflow', () => ({
  default: vi.fn(({ children, onNodeClick, nodes }) => (
    <div
      data-testid="react-flow"
      onClick={() => nodes?.[0] && onNodeClick?.({}, nodes[0])}
    >
      {children}
    </div>
  )),
  MiniMap: () => <div data-testid="minimap" />,
  Controls: () => <div data-testid="controls" />,
  Background: () => <div data-testid="background" />,
}));

vi.mock('reactflow/dist/style.css', () => ({}));

const mockExportAsPng = vi.fn().mockResolvedValue(undefined);
const mockExportAsSvg = vi.fn().mockResolvedValue(undefined);
vi.mock('../utils/exportGraph', () => ({
  exportAsPng: (...args) => mockExportAsPng(...args),
  exportAsSvg: (...args) => mockExportAsSvg(...args),
}));

vi.mock('./CustomNode', () => ({
  default: ({ data }) => <div data-testid="custom-node">{data?.label}</div>,
}));

const mockAddToast = vi.fn();
vi.mock('../hooks/useToast', () => ({
  useToast: () => mockAddToast,
}));

function renderViewer(props = {}) {
  const defaults = {
    nodes: [],
    edges: [],
    onNodesChange: vi.fn(),
    onEdgesChange: vi.fn(),
    onNodeClick: vi.fn(),
  };
  return render(<GraphViewer {...defaults} {...props} />);
}

describe('GraphViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the ReactFlow canvas', () => {
    renderViewer();
    expect(screen.getByTestId('react-flow')).toBeInTheDocument();
  });

  it('shows an upload-first empty state when no graph has been loaded yet', () => {
    const onRequestUpload = vi.fn();
    renderViewer({ onRequestUpload });

    expect(screen.getByText('Visualize any Python codebase')).toBeInTheDocument();
    expect(screen.getByText('Upload your Python project')).toBeInTheDocument();
    // Feature cards
    expect(screen.getByText('AI Explanations')).toBeInTheDocument();
    expect(screen.getByText('Ghost Runner')).toBeInTheDocument();
    expect(screen.getByText('Code Chat')).toBeInTheDocument();
  });

  it('calls onRequestUpload when the empty state CTA is clicked', async () => {
    const user = userEvent.setup();
    const onRequestUpload = vi.fn();
    renderViewer({ onRequestUpload });

    await user.click(screen.getByText('Upload your Python project'));
    expect(onRequestUpload).toHaveBeenCalledTimes(1);
  });

  it('renders PNG export button', () => {
    renderViewer();
    expect(screen.getByTitle('Export as PNG')).toBeInTheDocument();
  });

  it('renders SVG export button', () => {
    renderViewer();
    expect(screen.getByTitle('Export as SVG')).toBeInTheDocument();
  });

  it('calls exportAsPng and shows success toast when PNG button is clicked', async () => {
    const user = userEvent.setup();
    renderViewer();

    await user.click(screen.getByTitle('Export as PNG'));

    await waitFor(() => {
      expect(mockExportAsPng).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith('Graph exported as PNG', 'success');
    });
  });

  it('calls exportAsSvg and shows success toast when SVG button is clicked', async () => {
    const user = userEvent.setup();
    renderViewer();

    await user.click(screen.getByTitle('Export as SVG'));

    await waitFor(() => {
      expect(mockExportAsSvg).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith('Graph exported as SVG', 'success');
    });
  });

  it('shows error toast when PNG export fails', async () => {
    const user = userEvent.setup();
    mockExportAsPng.mockRejectedValueOnce(new Error('Canvas error'));
    renderViewer();

    await user.click(screen.getByTitle('Export as PNG'));

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith('PNG export failed', 'error');
    });
  });

  it('shows error toast when SVG export fails', async () => {
    const user = userEvent.setup();
    mockExportAsSvg.mockRejectedValueOnce(new Error('SVG error'));
    renderViewer();

    await user.click(screen.getByTitle('Export as SVG'));

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith('SVG export failed', 'error');
    });
  });

  it('calls onNodeClick when a node is clicked', async () => {
    const user = userEvent.setup();
    const onNodeClick = vi.fn();
    renderViewer({
      nodes: [{ id: 'main', data: { label: 'main' }, position: { x: 0, y: 0 } }],
      onNodeClick,
    });

    await user.click(screen.getByTestId('react-flow'));
    expect(onNodeClick).toHaveBeenCalled();
  });
});
