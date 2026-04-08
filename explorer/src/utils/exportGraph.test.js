import { describe, it, expect, vi, beforeEach } from 'vitest';
import { exportAsPng, exportAsSvg } from './exportGraph';

// Mock html-to-image
vi.mock('html-to-image', () => ({
    toPng: vi.fn(),
    toSvg: vi.fn(),
}));

import { toPng, toSvg } from 'html-to-image';

describe('exportGraph utilities', () => {
    let mockElement;
    let clickSpy;

    beforeEach(() => {
        vi.restoreAllMocks();
        mockElement = document.createElement('div');
        clickSpy = vi.fn();

        vi.spyOn(document, 'createElement').mockImplementation((tag) => {
            if (tag === 'a') {
                return { download: '', href: '', click: clickSpy };
            }
            // Fall through to real implementation for non-anchor elements
            return document.createElementNS('http://www.w3.org/1999/xhtml', tag);
        });
    });

    describe('exportAsPng', () => {
        it('exists and is a function', () => {
            expect(typeof exportAsPng).toBe('function');
        });

        it('calls toPng with the element and creates a download link', async () => {
            toPng.mockResolvedValue('data:image/png;base64,abc123');

            await exportAsPng(mockElement);

            expect(toPng).toHaveBeenCalledWith(mockElement, {
                quality: 1,
                pixelRatio: 2,
                backgroundColor: '#080a0f',
            });
            expect(clickSpy).toHaveBeenCalled();
        });

        it('propagates errors from toPng', async () => {
            toPng.mockRejectedValue(new Error('Render failed'));

            await expect(exportAsPng(mockElement)).rejects.toThrow('Render failed');
        });
    });

    describe('exportAsSvg', () => {
        it('exists and is a function', () => {
            expect(typeof exportAsSvg).toBe('function');
        });

        it('calls toSvg with the element and creates a download link', async () => {
            toSvg.mockResolvedValue('data:image/svg+xml;base64,xyz789');

            await exportAsSvg(mockElement);

            expect(toSvg).toHaveBeenCalledWith(mockElement, {
                backgroundColor: '#080a0f',
            });
            expect(clickSpy).toHaveBeenCalled();
        });

        it('propagates errors from toSvg', async () => {
            toSvg.mockRejectedValue(new Error('SVG render failed'));

            await expect(exportAsSvg(mockElement)).rejects.toThrow('SVG render failed');
        });
    });

    describe('edge cases', () => {
        it('handles null element by propagating the error from html-to-image', async () => {
            toPng.mockRejectedValue(new TypeError('Cannot read properties of null'));

            await expect(exportAsPng(null)).rejects.toThrow();
        });

        it('returns a promise (async function)', () => {
            toPng.mockResolvedValue('data:image/png;base64,test');
            const result = exportAsPng(mockElement);
            expect(result).toBeInstanceOf(Promise);
        });
    });
});
