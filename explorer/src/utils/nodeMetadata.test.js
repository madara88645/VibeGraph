import { describe, expect, it } from 'vitest';

import { buildNodeCodeContext } from './nodeMetadata';

describe('buildNodeCodeContext', () => {
  it('maps graph node metadata to backend code context fields', () => {
    const context = buildNodeCodeContext({
      id: 'greet',
      data: {
        file: 'src/greet.js',
        language: 'javascript',
        lineno: 3,
        end_lineno: 5,
      },
    });

    expect(context).toEqual({
      file_path: 'src/greet.js',
      language: 'javascript',
      start_line: 3,
      end_line: 5,
    });
  });

  it('falls back to original_data when node data is wrapped by React Flow', () => {
    const context = buildNodeCodeContext({
      id: 'Widget.render',
      data: {
        original_data: {
          file: 'src/widget.tsx',
          language: 'typescript',
          lineno: 10,
          end_lineno: 14,
        },
      },
    });

    expect(context).toEqual({
      file_path: 'src/widget.tsx',
      language: 'typescript',
      start_line: 10,
      end_line: 14,
    });
  });
});
