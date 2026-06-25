import { afterEach, describe, expect, it, vi } from 'vitest';

import { loadDemoGraph } from './loadDemoGraph';

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
