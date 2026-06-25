import { afterEach, describe, expect, it, vi } from 'vitest';

import { loadDemoAiContent, loadDemoGraph } from './loadDemoGraph';

afterEach(() => {
    vi.restoreAllMocks();
});

describe('loadDemoGraph', () => {
    it('fetches and returns the primary demo graph payload', async () => {
        const payload = { nodes: [{ id: 'a' }], edges: [] };
        const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
            ok: true,
            json: async () => payload,
        });

        const result = await loadDemoGraph();

        expect(fetchSpy).toHaveBeenCalledWith('/demo_graph_data.json');
        expect(result).toEqual(payload);
    });

    it('falls back to /graph_data.json when the primary file is missing', async () => {
        const payload = { nodes: [], edges: [] };
        const fetchSpy = vi
            .spyOn(globalThis, 'fetch')
            .mockResolvedValueOnce({ ok: false, status: 404 })
            .mockResolvedValueOnce({ ok: true, json: async () => payload });

        const result = await loadDemoGraph();

        expect(fetchSpy).toHaveBeenNthCalledWith(1, '/demo_graph_data.json');
        expect(fetchSpy).toHaveBeenNthCalledWith(2, '/graph_data.json');
        expect(result).toEqual(payload);
    });

    it('throws a descriptive error when no demo file is available', async () => {
        vi.spyOn(globalThis, 'fetch').mockResolvedValue({ ok: false, status: 500 });

        await expect(loadDemoGraph()).rejects.toThrow(/Demo file not found.*500/);
    });
});

describe('loadDemoAiContent', () => {
    it('fetches and returns the demo AI content', async () => {
        const payload = { version: 1, explanations: {}, chat: [] };
        const fetchSpy = vi
            .spyOn(globalThis, 'fetch')
            .mockResolvedValue({ ok: true, json: async () => payload });

        const result = await loadDemoAiContent();

        expect(fetchSpy).toHaveBeenCalledWith('/demo_ai_content.json');
        expect(result).toEqual(payload);
    });

    it('returns null (no throw) when the artifact is missing', async () => {
        vi.spyOn(globalThis, 'fetch').mockResolvedValue({ ok: false, status: 404 });
        await expect(loadDemoAiContent()).resolves.toBeNull();
    });

    it('returns null (no throw) when fetch rejects', async () => {
        vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('network down'));
        await expect(loadDemoAiContent()).resolves.toBeNull();
    });
});
