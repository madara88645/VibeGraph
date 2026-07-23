import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

import CustomNode from './CustomNode';

// reactflow's <Handle> throws when rendered outside a ReactFlow provider, and
// the graph runtime is irrelevant to the type/language rendering under test.
// Stub the two symbols CustomNode imports so the node renders standalone.
vi.mock('reactflow', () => ({
  Handle: () => null,
  Position: { Top: 'top', Bottom: 'bottom' },
}));

const renderNode = (data) => render(<CustomNode data={data} />);

// Icons are inline SVGs (components/icons.jsx) rather than text glyphs, so
// they are identified by the `data-icon` name their component stamps on.
const icon = (container, name) => container.querySelector(`[data-icon="${name}"]`);

describe('CustomNode', () => {
  it('renders the node label', () => {
    renderNode({ label: 'my_function' });

    expect(screen.getByText('my_function')).toBeInTheDocument();
  });

  describe('type badge', () => {
    it('renders the entry-point icon and badge when data.entry_point is true, regardless of data.type', () => {
      const { container } = renderNode({ label: 'main', entry_point: true, type: 'function' });

      // entry_point takes precedence over type: it must show the entry icon /
      // "entry" config, never the function config's icon / "fn".
      expect(icon(container, 'entry')).toBeInTheDocument();
      expect(icon(container, 'function')).not.toBeInTheDocument();
      expect(screen.getByText('entry')).toBeInTheDocument();
      expect(screen.queryByText('fn')).not.toBeInTheDocument();
    });

    it('falls back to the default config (badge "ref") for an unknown type', () => {
      const { container } = renderNode({ label: 'mystery', type: 'totally_unknown_type' });

      expect(screen.getByText('ref')).toBeInTheDocument();
      expect(icon(container, 'dot')).toBeInTheDocument();
    });
  });

  describe('language pill', () => {
    it('defaults to PY when no language is provided', () => {
      renderNode({ label: 'a' });

      expect(screen.getByText('PY')).toBeInTheDocument();
    });

    it('shows PY for an unrecognised language', () => {
      renderNode({ label: 'a', language: 'ruby' });

      expect(screen.getByText('PY')).toBeInTheDocument();
    });

    it('shows JS when language is javascript', () => {
      renderNode({ label: 'a', language: 'javascript' });

      expect(screen.getByText('JS')).toBeInTheDocument();
      expect(screen.queryByText('PY')).not.toBeInTheDocument();
    });

    it('shows TS when language is typescript', () => {
      renderNode({ label: 'a', language: 'typescript' });

      expect(screen.getByText('TS')).toBeInTheDocument();
      expect(screen.queryByText('PY')).not.toBeInTheDocument();
    });
  });

  describe('meta row', () => {
    it('renders the shortened filename and line number when file and lineno are present', () => {
      renderNode({ label: 'a', file: 'src/deep/nested/module.py', lineno: 42 });

      expect(screen.getByText('module.py')).toBeInTheDocument();
      expect(screen.getByText('L42')).toBeInTheDocument();
    });

    it('omits the meta row when neither file nor lineno is present', () => {
      const { container } = renderNode({ label: 'a' });

      expect(icon(container, 'file')).not.toBeInTheDocument();
      expect(screen.queryByText(/^L\d+$/)).not.toBeInTheDocument();
    });
  });
});
