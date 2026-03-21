import test from 'node:test';
import assert from 'node:assert/strict';

import { consumeSseChunk } from './sse.js';

test('consumeSseChunk joins multiline data fields and handles CRLF', () => {
    const { buffer, events } = consumeSseChunk('', 'data: line one\r\ndata: line two\r\n\r\n');

    assert.equal(buffer, '');
    assert.deepEqual(events, ['line one\nline two']);
});

test('consumeSseChunk keeps trailing partial event data in buffer', () => {
    const first = consumeSseChunk('', 'data: par');
    assert.equal(first.buffer, 'data: par');
    assert.deepEqual(first.events, []);

    const second = consumeSseChunk(first.buffer, 'tial\n\ndata: done\n\n');
    assert.equal(second.buffer, '');
    assert.deepEqual(second.events, ['partial', 'done']);
});
