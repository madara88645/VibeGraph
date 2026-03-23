export function consumeSseChunk(buffer, chunk) {
    const normalized = `${buffer}${chunk}`.replace(/\r\n/g, '\n');
    const segments = normalized.split('\n\n');
    const remainder = segments.pop() ?? '';
    const events = [];

    for (const segment of segments) {
        const dataLines = segment
            .split('\n')
            .filter((line) => line.startsWith('data:'))
            .map((line) => {
                let value = line.slice(5);
                if (value.startsWith(' ')) {
                    value = value.slice(1);
                }
                return value;
            });

        if (dataLines.length > 0) {
            events.push(dataLines.join('\n'));
        }
    }

    return { buffer: remainder, events };
}
