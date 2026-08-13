import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const cssPath = resolve(dirname(fileURLToPath(import.meta.url)), 'index.css');
const cssSource = readFileSync(cssPath, 'utf8');

function extractAtRuleBlocks(css, prelude) {
  const blocks = [];
  let from = 0;

  while (from < css.length) {
    const start = css.indexOf(prelude, from);
    if (start === -1) {
      break;
    }

    const open = css.indexOf('{', start);
    let depth = 0;
    let closedAt = -1;
    for (let i = open; i < css.length; i += 1) {
      if (css[i] === '{') {
        depth += 1;
      } else if (css[i] === '}') {
        depth -= 1;
        if (depth === 0) {
          closedAt = i;
          break;
        }
      }
    }

    if (closedAt === -1) {
      throw new Error(`Unclosed block for ${prelude}`);
    }

    blocks.push(css.slice(open + 1, closedAt));
    from = closedAt + 1;
  }

  if (blocks.length === 0) {
    throw new Error(`Missing ${prelude}`);
  }

  return blocks;
}

function extractAtRuleBlock(css, prelude) {
  return extractAtRuleBlocks(css, prelude)[0];
}

function extractRule(block, selector) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = block.match(new RegExp(`${escaped}\\s*\\{([^}]*)\\}`));
  if (!match) {
    throw new Error(`Missing ${selector} rule`);
  }
  return match[1];
}

describe('header layout at 1440px (issue #438)', () => {
  it('keeps .vibe-header on one row by default', () => {
    const rule = extractRule(cssSource, '.vibe-header');
    expect(rule).toMatch(/flex-wrap:\s*nowrap/);
    expect(rule).not.toMatch(/flex-wrap:\s*wrap/);
  });

  it('does not wrap the header in the 1200px media query', () => {
    const block = extractAtRuleBlock(cssSource, '@media (max-width: 1200px)');
    const headerRule = extractRule(block, '.vibe-header');
    expect(headerRule).toMatch(/flex-wrap:\s*nowrap/);
    expect(headerRule).not.toMatch(/flex-wrap:\s*wrap/);
  });

  it('does not wrap the header when the explanation panel is open on desktop', () => {
    const block = extractAtRuleBlock(cssSource, '@media (min-width: 769px)');
    const headerRule = extractRule(block, '.vibe-header-panel-open');
    expect(headerRule).toMatch(/flex-wrap:\s*nowrap/);
    expect(headerRule).not.toMatch(/flex-wrap:\s*wrap/);
  });

  it('lets the search bar shrink instead of forcing a second row', () => {
    const rule = extractRule(cssSource, '.search-bar');
    expect(rule).toMatch(/min-width:\s*0/);
    expect(rule).toMatch(/flex:\s*1 1/);
  });

  it('still wraps the header at the mobile breakpoint', () => {
    const wrapsOnMobile = extractAtRuleBlocks(cssSource, '@media (max-width: 768px)').some((block) => {
      try {
        return /flex-wrap:\s*wrap/.test(extractRule(block, '.vibe-header'));
      } catch {
        return false;
      }
    });
    expect(wrapsOnMobile).toBe(true);
  });
});
