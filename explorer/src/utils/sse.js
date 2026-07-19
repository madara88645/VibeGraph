export function consumeSseChunk(buffer, chunk) {
    const normalized = `${buffer}${chunk}`.replace(/\r\n/g, '\n');
    const segments = normalized.split('\n\n');
    const remainder = segments.pop() ?? '';
    const events = [];

    for (const segment of segments) {
        // PERFORMANCE OPTIMIZATION (Bolt): Replace .filter().map() chain with a single
        // imperative loop to eliminate intermediate array allocations during high-frequency
        // SSE chunk parsing, reducing garbage collection pressure.
        const lines = segment.split('\n');
        const dataLines = [];
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            if (line.startsWith('data:')) {
                let value = line.slice(5);
                if (value.startsWith(' ')) {
                    value = value.slice(1);
                }
                dataLines.push(value);
            }
        }

        if (dataLines.length > 0) {
            events.push(dataLines.join('\n'));
        }
    }

    return { buffer: remainder, events };
}
