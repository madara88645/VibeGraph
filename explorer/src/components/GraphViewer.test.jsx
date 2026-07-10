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
  const graphNode = { id: 'main', data: { label: 'main' }, position: { x: 0, y: 0 } };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the ReactFlow canvas', () => {
    renderViewer();
    expect(screen.getByTestId('react-flow')).toBeInTheDocument();
  });

  it('shows an outcome-led empty state when no graph has been loaded yet', () => {
    const onRequestUpload = vi.fn();
    renderViewer({ onRequestUpload });

    expect(screen.getByText('Understand any codebase in minutes')).toBeInTheDocument();
    expect(screen.getByText('Upload your project')).toBeInTheDocument();
    // Feature cards
    expect(screen.getByText('AI Explanations')).toBeInTheDocument();
    expect(screen.getByText('Ghost Runner')).toBeInTheDocument();
    expect(screen.getByText('Code Chat')).toBeInTheDocument();
  });

  it('calls onRequestUpload when the empty state CTA is clicked', async () => {
    const user = userEvent.setup();
    const onRequestUpload = vi.fn();
    renderViewer({ onRequestUpload });

    await user.click(screen.getByText('Upload your project'));
    expect(onRequestUpload).toHaveBeenCalledTimes(1);
  });

  it('offers a zero-setup live demo CTA in the empty state', () => {
    renderViewer({ onLoadDemo: vi.fn() });

    expect(screen.getByRole('button', { name: /see a live demo/i })).toBeInTheDocument();
  });

  it('calls onLoadDemo when the live demo CTA is clicked', async () => {
    const user = userEvent.setup();
    const onLoadDemo = vi.fn();
    renderViewer({ onLoadDemo });

    await user.click(screen.getByRole('button', { name: /see a live demo/i }));
    expect(onLoadDemo).toHaveBeenCalledTimes(1);
  });

  it('does not render export controls before a graph is loaded', () => {
    renderViewer();

    expect(screen.queryByRole('button', { name: 'Export' })).not.toBeInTheDocument();
    expect(screen.queryByRole('menuitem', { name: 'Export as PNG' })).not.toBeInTheDocument();
    expect(screen.queryByRole('menuitem', { name: 'Export as SVG' })).not.toBeInTheDocument();
  });

  it('renders a single export trigger once a graph exists', () => {
    renderViewer({ nodes: [graphNode] });

    expect(screen.getByRole('button', { name: 'Export' })).toBeInTheDocument();
    expect(screen.queryByRole('menuitem', { name: 'Export as PNG' })).not.toBeInTheDocument();
    expect(screen.queryByRole('menuitem', { name: 'Export as SVG' })).not.toBeInTheDocument();
  });

  it('reveals PNG and SVG actions when export is opened', async () => {
    const user = userEvent.setup();
    renderViewer({ nodes: [graphNode] });

    await user.click(screen.getByRole('button', { name: 'Export' }));

    expect(screen.getByRole('menuitem', { name: 'Export as PNG' })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: 'Export as SVG' })).toBeInTheDocument();
  });

  it('calls exportAsPng and shows success toast when PNG button is clicked', async () => {
    const user = userEvent.setup();
    renderViewer({ nodes: [graphNode] });

    await user.click(screen.getByRole('button', { name: 'Export' }));
    await user.click(screen.getByRole('menuitem', { name: 'Export as PNG' }));

    await waitFor(() => {
      expect(mockExportAsPng).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith('Graph exported as PNG', 'success');
    });
  });

  it('calls exportAsSvg and shows success toast when SVG button is clicked', async () => {
    const user = userEvent.setup();
    renderViewer({ nodes: [graphNode] });

    await user.click(screen.getByRole('button', { name: 'Export' }));
    await user.click(screen.getByRole('menuitem', { name: 'Export as SVG' }));

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
    renderViewer({ nodes: [graphNode] });

    await user.click(screen.getByRole('button', { name: 'Export' }));
    await user.click(screen.getByRole('menuitem', { name: 'Export as PNG' }));

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith('PNG export failed', 'error');
    });
  });

  it('shows error toast when SVG export fails', async () => {
    const user = userEvent.setup();
    mockExportAsSvg.mockRejectedValueOnce(new Error('SVG error'));
    renderViewer({ nodes: [graphNode] });

    await user.click(screen.getByRole('button', { name: 'Export' }));
    await user.click(screen.getByRole('menuitem', { name: 'Export as SVG' }));

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith('SVG export failed', 'error');
    });
  });

  it('closes the export menu after choosing PNG', async () => {
    const user = userEvent.setup();
    renderViewer({ nodes: [graphNode] });

    await user.click(screen.getByRole('button', { name: 'Export' }));
    await user.click(screen.getByRole('menuitem', { name: 'Export as PNG' }));

    await waitFor(() => {
      expect(mockExportAsPng).toHaveBeenCalled();
    });
    expect(screen.queryByRole('menuitem', { name: 'Export as PNG' })).not.toBeInTheDocument();
  });

  it('closes the export menu when Escape key is pressed', async () => {
    const user = userEvent.setup();
    renderViewer({ nodes: [graphNode] });

    await user.click(screen.getByRole('button', { name: 'Export' }));
    expect(screen.getByRole('menuitem', { name: 'Export as PNG' })).toBeInTheDocument();

    await user.keyboard('{Escape}');
    expect(screen.queryByRole('menuitem', { name: 'Export as PNG' })).not.toBeInTheDocument();
  });

  it('closes the export menu when clicking outside the export controls', async () => {
    const user = userEvent.setup();
    renderViewer({ nodes: [graphNode] });

    await user.click(screen.getByRole('button', { name: 'Export' }));
    expect(screen.getByRole('menuitem', { name: 'Export as PNG' })).toBeInTheDocument();

    await user.click(screen.getByTestId('react-flow'));
    expect(screen.queryByRole('menuitem', { name: 'Export as PNG' })).not.toBeInTheDocument();
  });


  it('calls onNodeClick when a node is clicked', async () => {
    const user = userEvent.setup();
    const onNodeClick = vi.fn();
    renderViewer({
      nodes: [graphNode],
      onNodeClick,
    });

    await user.click(screen.getByTestId('react-flow'));
    expect(onNodeClick).toHaveBeenCalled();
  });

  it('shows a summary warning when the uploaded graph was truncated', () => {
    renderViewer({
      nodes: [graphNode],
      graphMeta: {
        truncated: true,
        kept_nodes: 1500,
        total_nodes: 2143,
      },
    });

    expect(
      screen.getByText('Showing 1500 of 2143 nodes. This is a summary view for a very large graph.')
    ).toBeInTheDocument();
  });
});
