function createDownloadLink(dataUrl, filename) {
    const link = document.createElement('a');
    link.download = filename;
    link.href = dataUrl;
    link.click();
}

function elementToSvgString(element, backgroundColor = '#080a0f') {
    const rect = element.getBoundingClientRect();
    const width = rect.width || element.offsetWidth || 800;
    const height = rect.height || element.offsetHeight || 600;

    if (element instanceof SVGElement) {
        const serializer = new XMLSerializer();
        let svgString = serializer.serializeToString(element);

        if (!/width=/.test(svgString) || !/height=/.test(svgString)) {
            svgString = svgString.replace(
                '<svg',
                `<svg width="${width}" height="${height}"`
            );
        }

        if (!/<rect[\s>]/.test(svgString) && backgroundColor) {
            svgString = svgString.replace(
                /(<svg[^>]*>)/,
                `$1<rect width="100%" height="100%" fill="${backgroundColor}" />`
            );
        }

        return svgString;
    }

    const serializer = new XMLSerializer();
    const xhtml = serializer.serializeToString(element);

    const svg =
        `<svg xmlns="http://www.w3.org/2000/svg" ` +
        `width="${width}" height="${height}">` +
        (backgroundColor
            ? `<rect width="100%" height="100%" fill="${backgroundColor}" />`
            : '') +
        `<foreignObject width="100%" height="100%">` +
        `<div xmlns="http://www.w3.org/1999/xhtml">` +
        xhtml +
        `</div>` +
        `</foreignObject>` +
        `</svg>`;

    return svg;
}

function svgStringToDataUrl(svgString) {
    const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    return URL.createObjectURL(blob);
}

function svgStringToPngDataUrl(svgString, width, height, backgroundColor = '#080a0f') {
    return new Promise((resolve, reject) => {
        const img = new Image();
        const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(svgBlob);

        img.onload = () => {
            try {
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');

                if (!ctx) {
                    URL.revokeObjectURL(url);
                    reject(new Error('Canvas 2D context not available'));
                    return;
                }

                if (backgroundColor) {
                    ctx.fillStyle = backgroundColor;
                    ctx.fillRect(0, 0, width, height);
                }

                ctx.drawImage(img, 0, 0, width, height);
                const pngDataUrl = canvas.toDataURL('image/png', 1.0);
                URL.revokeObjectURL(url);
                resolve(pngDataUrl);
            } catch (err) {
                URL.revokeObjectURL(url);
                reject(err);
            }
        };

        img.onerror = (err) => {
            URL.revokeObjectURL(url);
            reject(err);
        };

        img.src = url;
    });
}

export async function exportAsPng(element) {
    const rect = element.getBoundingClientRect();
    const width = rect.width || element.offsetWidth || 800;
    const height = rect.height || element.offsetHeight || 600;

    const svgString = elementToSvgString(element, '#080a0f');
    const dataUrl = await svgStringToPngDataUrl(svgString, width, height, '#080a0f');
    createDownloadLink(dataUrl, 'vibegraph.png');
}

export async function exportAsSvg(element) {
    const svgString = elementToSvgString(element, '#080a0f');
    const dataUrl = svgStringToDataUrl(svgString);
    createDownloadLink(dataUrl, 'vibegraph.svg');
}
