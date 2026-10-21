import { describe, expect, it } from 'vitest';

import { shouldSkipUploadPath } from './uploadFilter';

describe('shouldSkipUploadPath', () => {
  it('keeps a normal source file under the top-level folder', () => {
    expect(shouldSkipUploadPath('myproj/src/app.py')).toBe(false);
    expect(shouldSkipUploadPath('myproj/index.js')).toBe(false);
  });

  it('keeps .gitignore and other dotfiles that are not sensitive', () => {
    expect(shouldSkipUploadPath('myproj/.gitignore')).toBe(false);
    expect(shouldSkipUploadPath('myproj/.github/workflows/ci.yml')).toBe(false);
    expect(shouldSkipUploadPath('myproj/.eslintrc.js')).toBe(false);
  });

  it('skips .git contents under the top-level folder prefix', () => {
    expect(shouldSkipUploadPath('myproj/.git/config')).toBe(true);
    expect(shouldSkipUploadPath('myproj/.git/objects/ab/cdef')).toBe(true);
    expect(shouldSkipUploadPath('myproj/vendor/lib/.git')).toBe(true);
  });

  it('skips files in analyzer-ignored folders at any depth', () => {
    expect(shouldSkipUploadPath('myproj/node_modules/react/index.js')).toBe(true);
    expect(shouldSkipUploadPath('myproj/packages/web/node_modules/x/lib/a.js')).toBe(true);
    expect(shouldSkipUploadPath('myproj/.venv/lib/python3.12/site-packages/x.py')).toBe(true);
    expect(shouldSkipUploadPath('myproj/app/__pycache__/main.cpython-312.pyc')).toBe(true);
    expect(shouldSkipUploadPath('myproj/env/bin/activate')).toBe(true);
    expect(shouldSkipUploadPath('myproj/venv/lib/site.py')).toBe(true);
  });

  it('keeps build output folders the analyzer still reads', () => {
    expect(shouldSkipUploadPath('myproj/build/lib/app.py')).toBe(false);
    expect(shouldSkipUploadPath('myproj/dist/index.js')).toBe(false);
  });

  it('only treats ignored names as folders, not as file names', () => {
    expect(shouldSkipUploadPath('myproj/scripts/env')).toBe(false);
    expect(shouldSkipUploadPath('myproj/src/env.py')).toBe(false);
  });

  it('matches analyzer-ignored folders case-sensitively, like the analyzer', () => {
    expect(shouldSkipUploadPath('myproj/Node_Modules/x/index.js')).toBe(false);
  });

  it('skips .env files and anything starting with .env', () => {
    expect(shouldSkipUploadPath('myproj/.env')).toBe(true);
    expect(shouldSkipUploadPath('myproj/.env.local')).toBe(true);
    expect(shouldSkipUploadPath('myproj/.env.example')).toBe(true);
    expect(shouldSkipUploadPath('myproj/.envrc')).toBe(true);
    expect(shouldSkipUploadPath('myproj/config/.env.production/settings.py')).toBe(true);
  });

  it('skips sensitive files and folders the backend refuses', () => {
    expect(shouldSkipUploadPath('myproj/.npmrc')).toBe(true);
    expect(shouldSkipUploadPath('myproj/.pypirc')).toBe(true);
    expect(shouldSkipUploadPath('myproj/.netrc')).toBe(true);
    expect(shouldSkipUploadPath('myproj/.ssh/known_hosts')).toBe(true);
    expect(shouldSkipUploadPath('myproj/.aws/credentials')).toBe(true);
  });

  it('skips private-key-like files', () => {
    expect(shouldSkipUploadPath('myproj/deploy/id_rsa')).toBe(true);
    expect(shouldSkipUploadPath('myproj/id_ed25519')).toBe(true);
    expect(shouldSkipUploadPath('myproj/certs/server.pem')).toBe(true);
    expect(shouldSkipUploadPath('myproj/certs/server.key')).toBe(true);
    expect(shouldSkipUploadPath('myproj/deploy/id_rsa.pub')).toBe(false);
  });

  it('matches sensitive names case-insensitively, like the backend', () => {
    expect(shouldSkipUploadPath('myproj/.ENV.Local')).toBe(true);
    expect(shouldSkipUploadPath('myproj/.Git/HEAD')).toBe(true);
    expect(shouldSkipUploadPath('myproj/.SSH/config')).toBe(true);
    expect(shouldSkipUploadPath('myproj/ID_RSA')).toBe(true);
    expect(shouldSkipUploadPath('myproj/certs/Server.PEM')).toBe(true);
  });

  it('handles backslash separators', () => {
    expect(shouldSkipUploadPath('myproj\\node_modules\\x\\index.js')).toBe(true);
    expect(shouldSkipUploadPath('myproj\\.git\\config')).toBe(true);
    expect(shouldSkipUploadPath('myproj\\src\\app.py')).toBe(false);
  });

  it('keeps a bare file name and empty input', () => {
    expect(shouldSkipUploadPath('project.zip')).toBe(false);
    expect(shouldSkipUploadPath('main.py')).toBe(false);
    expect(shouldSkipUploadPath('')).toBe(false);
    expect(shouldSkipUploadPath(undefined)).toBe(false);
  });
});
