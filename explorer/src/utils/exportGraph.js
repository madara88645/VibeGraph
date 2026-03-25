import { toPng, toSvg } from 'html-to-image';

export async function exportAsPng(element) {
    const dataUrl = await toPng(element, { quality: 1, pixelRatio: 2, backgroundColor: '#080a0f' });
    const link = document.createElement('a');
    link.download = 'vibegraph.png';
    link.href = dataUrl;
    link.click();
}

export async function exportAsSvg(element) {
    const dataUrl = await toSvg(element, { backgroundColor: '#080a0f' });
    const link = document.createElement('a');
    link.download = 'vibegraph.svg';
    link.href = dataUrl;
    link.click();
}
