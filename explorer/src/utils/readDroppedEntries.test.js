import { describe, expect, it, vi } from 'vitest';

import { readDroppedEntries } from './readDroppedEntries';

function fileEntry(fullPath) {
  const name = fullPath.split('/').pop();
  const file = new File(['content'], name, { type: 'text/plain' });
  return {
    isFile: true,
    isDirectory: false,
    name,
    fullPath,
    file: vi.fn((resolve) => resolve(file)),
  };
}

// Mimics FileSystemDirectoryEntry: each reader hands out at most batchSize
// children per readEntries() call, then an empty batch.
function directoryEntry(fullPath, children = [], { batchSize = Infinity, readError } = {}) {
  const readers = [];
  const entry = {
    isFile: false,
    isDirectory: true,
    name: fullPath.split('/').pop(),
    fullPath,
    readers,
    createReader: vi.fn(() => {
      let offset = 0;
      const reader = {
        readEntries: vi.fn((resolve, reject) => {
          if (readError) {
            reject(readError);
            return;
          }
          const batch = children.slice(offset, offset + batchSize);
          offset += batch.length;
          resolve(batch);
        }),
      };
      readers.push(reader);
      return reader;
    }),
  };
  return entry;
}

const pathsOf = (collected) => collected.map(({ path }) => path);

describe('readDroppedEntries', () => {
  it('walks nested folders and returns paths relative to the dropped folder', async () => {
    const root = directoryEntry('/myproj', [
      fileEntry('/myproj/main.py'),
      directoryEntry('/myproj/src', [
        fileEntry('/myproj/src/app.py'),
        directoryEntry('/myproj/src/utils', [fileEntry('/myproj/src/utils/helpers.py')]),
      ]),
    ]);

    const collected = await readDroppedEntries([root]);

    expect(pathsOf(collected)).toEqual([
      'myproj/main.py',
      'myproj/src/app.py',
      'myproj/src/utils/helpers.py',
    ]);
    expect(collected.every(({ file }) => file instanceof File)).toBe(true);
    expect(collected[2].file.name).toBe('helpers.py');
  });

  it('keeps calling readEntries until the folder returns an empty batch', async () => {
    const root = directoryEntry(
      '/myproj',
      ['a.py', 'b.py', 'c.py', 'd.py'].map((name) => fileEntry(`/myproj/${name}`)),
      { batchSize: 2 },
    );

    const collected = await readDroppedEntries([root]);

    expect(pathsOf(collected)).toEqual(['myproj/a.py', 'myproj/b.py', 'myproj/c.py', 'myproj/d.py']);
    expect(root.createReader).toHaveBeenCalledTimes(1);
    expect(root.readers[0].readEntries).toHaveBeenCalledTimes(3);
  });

  it('reads a folder that comes back in one very large batch', async () => {
    // Firefox and Safari can return every child from the first readEntries()
    // call, e.g. a dataset folder with 150k images.
    const file = new File(['content'], 'img.png');
    const children = Array.from({ length: 150_000 }, (_, i) => ({
      isFile: true,
      isDirectory: false,
      name: `${i}.png`,
      fullPath: `/myproj/data/${i}.png`,
      file: (resolve) => resolve(file),
    }));

    const collected = await readDroppedEntries([directoryEntry('/myproj/data', children)]);

    expect(collected).toHaveLength(150_000);
    expect(collected[149_999].path).toBe('myproj/data/149999.png');
  });

  it('never opens folders the upload would skip', async () => {
    const nodeModules = directoryEntry('/myproj/node_modules', [fileEntry('/myproj/node_modules/react/index.js')]);
    const nestedNodeModules = directoryEntry('/myproj/packages/web/node_modules', [
      fileEntry('/myproj/packages/web/node_modules/x/index.js'),
    ]);
    const git = directoryEntry('/myproj/.git', [fileEntry('/myproj/.git/HEAD')]);
    const venv = directoryEntry('/myproj/.venv', [fileEntry('/myproj/.venv/pyvenv.cfg')]);
    const root = directoryEntry('/myproj', [
      nodeModules,
      git,
      venv,
      directoryEntry('/myproj/packages', [
        directoryEntry('/myproj/packages/web', [nestedNodeModules, fileEntry('/myproj/packages/web/index.js')]),
      ]),
      fileEntry('/myproj/.gitignore'),
    ]);

    const collected = await readDroppedEntries([root]);

    expect(pathsOf(collected)).toEqual(['myproj/packages/web/index.js', 'myproj/.gitignore']);
    for (const skipped of [nodeModules, nestedNodeModules, git, venv]) {
      expect(skipped.createReader).not.toHaveBeenCalled();
    }
  });

  it('keeps loose files dropped next to a folder at their own name', async () => {
    const collected = await readDroppedEntries([
      directoryEntry('/src', [fileEntry('/src/app.py')]),
      fileEntry('/main.py'),
    ]);

    expect(pathsOf(collected)).toEqual(['src/app.py', 'main.py']);
  });

  it('rejects when a folder cannot be read', async () => {
    const error = new DOMException('Folder went away', 'NotFoundError');
    const root = directoryEntry('/myproj', [
      fileEntry('/myproj/main.py'),
      directoryEntry('/myproj/src', [fileEntry('/myproj/src/app.py')], { readError: error }),
    ]);

    await expect(readDroppedEntries([root])).rejects.toBe(error);
  });

  it('rejects when a file cannot be read', async () => {
    const error = new DOMException('File went away', 'NotReadableError');
    const broken = fileEntry('/myproj/main.py');
    broken.file = vi.fn((resolve, reject) => reject(error));

    await expect(readDroppedEntries([directoryEntry('/myproj', [broken])])).rejects.toBe(error);
  });
});
