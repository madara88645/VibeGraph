export function buildNodeCodeContext(node) {
  const data = node?.data || {};
  const original = data.original_data || {};

  const filePath = data.file || original.file || null;
  const language = data.language || original.language || null;
  const startLine = data.lineno ?? data.start_line ?? original.lineno ?? original.start_line ?? null;
  const endLine = data.end_lineno ?? data.end_line ?? original.end_lineno ?? original.end_line ?? null;

  return {
    file_path: filePath,
    language,
    start_line: startLine,
    end_line: endLine,
  };
}
