import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const cssPath = resolve(dirname(fileURLToPath(import.meta.url)), 'index.css');
const cssSource = readFileSync(cssPath, 'utf8');

function getLightThemeVariables() {
  const match = cssSource.match(/\[data-theme="light"\]\s*\{([\s\S]*?)\n\}/);

  if (!match) {
    throw new Error('Light theme block not found in index.css');
  }

  return Object.fromEntries(
    [...match[1].matchAll(/--([^:]+):\s*([^;]+);/g)].map(([, name, value]) => [
      name.trim(),
      value.trim(),
    ])
  );
}

function hexToRgb(hex) {
  const normalized = hex.replace('#', '');
  const size = normalized.length === 3 ? 1 : 2;
  const values = normalized.match(new RegExp(`.{${size}}`, 'g'));

  if (!values) {
    throw new Error(`Invalid hex color: ${hex}`);
  }

  return values.map((part) => {
    const expanded = size === 1 ? `${part}${part}` : part;
    return Number.parseInt(expanded, 16) / 255;
  });
}

function linearizeChannel(channel) {
  return channel <= 0.03928
    ? channel / 12.92
    : ((channel + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(hex) {
  const [r, g, b] = hexToRgb(hex).map(linearizeChannel);
  return (0.2126 * r) + (0.7152 * g) + (0.0722 * b);
}

describe('light theme palette', () => {
  it('keeps the base canvas softer than near-white', () => {
    const vars = getLightThemeVariables();
    expect(relativeLuminance(vars['color-bg'])).toBeLessThan(0.88);
  });
});
