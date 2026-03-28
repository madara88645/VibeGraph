import { toPng, toSvg } from 'html-to-image';

function createDownloadLink(dataUrl, filename) {
  const link = document.createElement('a');
  link.download = filename;
  link.href = dataUrl;
  link.click();
}

export async function exportAsPng(element) {
  const dataUrl = await toPng(element, {
    quality: 1,
    pixelRatio: 2,
    backgroundColor: '#080a0f',
  });
  createDownloadLink(dataUrl, 'vibegraph.png');
}

export async function exportAsSvg(element) {
  const dataUrl = await toSvg(element, {
    backgroundColor: '#080a0f',
  });
  createDownloadLink(dataUrl, 'vibegraph.svg');
}
