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

describe('CustomNode', () => {
  it('renders the node label', () => {
    renderNode({ label: 'my_function' });

    expect(screen.getByText('my_function')).toBeInTheDocument();
  });

  describe('type badge', () => {
    it('renders the entry-point icon and badge when data.entry_point is true, regardless of data.type', () => {
      renderNode({ label: 'main', entry_point: true, type: 'function' });

      // entry_point takes precedence over type: it must show the 🚀 / "entry"
      // config, never the function config's ⚡ / "fn".
      expect(screen.getByText('🚀')).toBeInTheDocument();
      expect(screen.getByText('entry')).toBeInTheDocument();
      expect(screen.queryByText('fn')).not.toBeInTheDocument();
    });

    it('falls back to the default config (badge "ref") for an unknown type', () => {
      renderNode({ label: 'mystery', type: 'totally_unknown_type' });

      expect(screen.getByText('ref')).toBeInTheDocument();
      expect(screen.getByText('○')).toBeInTheDocument();
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
      renderNode({ label: 'a' });

      expect(screen.queryByText('📄')).not.toBeInTheDocument();
      expect(screen.queryByText(/^L\d+$/)).not.toBeInTheDocument();
    });
  });
});
