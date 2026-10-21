// Mirrors IGNORED_DIRS in analyst/analyzer.py (exact, case-sensitive names),
// so skipping these folders does not change the analysis result.
const ANALYZER_IGNORED_DIRS = new Set([
  '.git',
  'node_modules',
  'site-packages',
  'venv',
  'env',
  '.venv',
  '__pycache__',
]);

// normalize_uploaded_filename (app/utils/security.py) rejects the whole upload
// when any path segment matches one of these, or starts with ".env".
const SENSITIVE_SEGMENTS = new Set(['.env', '.git', '.ssh', '.aws', '.npmrc', '.pypirc', '.netrc']);

const PRIVATE_KEY_NAMES = new Set(['id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519']);
const PRIVATE_KEY_EXTENSIONS = ['.pem', '.key'];

function isSensitiveSegment(segment) {
  const lower = segment.toLowerCase();
  return lower.startsWith('.env') || SENSITIVE_SEGMENTS.has(lower);
}

function isPrivateKeyName(fileName) {
  const lower = fileName.toLowerCase();
  return PRIVATE_KEY_NAMES.has(lower) || PRIVATE_KEY_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

function splitUploadPath(relativePath) {
  return String(relativePath ?? '')
    .replace(/\\/g, '/')
    .split('/')
    .filter((segment) => segment !== '' && segment !== '.');
}

function hasSkippedDirectory(directories) {
  return directories.some((dir) => ANALYZER_IGNORED_DIRS.has(dir) || isSensitiveSegment(dir));
}

/**
 * Returns true when a file at this upload path should stay in the browser:
 * it lives in a folder the analyzer ignores, or it is a secret the backend
 * refuses (or should never receive).
 */
export function shouldSkipUploadPath(relativePath) {
  const segments = splitUploadPath(relativePath);
  if (segments.length === 0) return false;

  const fileName = segments[segments.length - 1];
  const directories = segments.slice(0, -1);

  return hasSkippedDirectory(directories) || isSensitiveSegment(fileName) || isPrivateKeyName(fileName);
}

/**
 * Returns true when shouldSkipUploadPath would skip every file under this
 * folder, so a folder walk can leave it unread (node_modules can hold 100k+
 * entries).
 */
export function shouldSkipUploadDirectory(relativePath) {
  return hasSkippedDirectory(splitUploadPath(relativePath));
}
