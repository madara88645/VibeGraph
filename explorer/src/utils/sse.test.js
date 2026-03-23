import { describe, it, expect } from 'vitest';
import { consumeSseChunk } from './sse.js';

describe('consumeSseChunk', () => {
    it('joins multiline data fields and handles CRLF', () => {
        const { buffer, events } = consumeSseChunk('', 'data: line one\r\ndata: line two\r\n\r\n');

        expect(buffer).toBe('');
        expect(events).toEqual(['line one\nline two']);
    });

    it('keeps trailing partial event data in buffer', () => {
        const first = consumeSseChunk('', 'data: par');
        expect(first.buffer).toBe('data: par');
        expect(first.events).toEqual([]);

        const second = consumeSseChunk(first.buffer, 'tial\n\ndata: done\n\n');
        expect(second.buffer).toBe('');
        expect(second.events).toEqual(['partial', 'done']);
    });
});
