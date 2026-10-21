import { shouldSkipUploadDirectory } from './uploadFilter';

// "/myproj/src/app.py" -> "myproj/src/app.py", the same shape webkitRelativePath
// gives for a folder picked with "Browse Folder".
function toRelativePath(entry) {
  return String(entry.fullPath || entry.name || '').replace(/^\/+/, '');
}

function readFile(fileEntry) {
  return new Promise((resolve, reject) => fileEntry.file(resolve, reject));
}

function readBatch(reader) {
  return new Promise((resolve, reject) => reader.readEntries(resolve, reject));
}

// Chromium returns at most 100 entries per readEntries() call, so keep reading
// until an empty batch says the folder is done.
async function readChildren(directoryEntry) {
  const reader = directoryEntry.createReader();
  const children = [];
  for (;;) {
    const batch = await readBatch(reader);
    if (batch.length === 0) return children;
    children.push(...batch);
  }
}

async function collect(entry) {
  const path = toRelativePath(entry);
  if (entry.isFile) {
    return [{ file: await readFile(entry), path }];
  }
  if (!entry.isDirectory || shouldSkipUploadDirectory(path)) {
    return [];
  }

  const children = await readChildren(entry);
  const nested = await Promise.all(children.map(collect));
  return nested.flat();
}

/**
 * Reads dropped FileSystemEntry objects (from DataTransferItem.webkitGetAsEntry)
 * into { file, path } pairs, walking folders recursively. Folders the upload
 * would skip anyway (node_modules, .git, .env*, ...) are never opened.
 * Rejects when the browser fails to read a folder or file.
 */
export async function readDroppedEntries(entries) {
  const nested = await Promise.all(Array.from(entries, collect));
  return nested.flat();
}
