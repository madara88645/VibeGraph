/** Small helpers used by API and UI layers. */

export function buildUserPayload(userId) {
  return { id: String(userId).trim() };
}

export function formatDisplayName(user) {
  if (!user?.name) {
    return `anonymous (${user?.id ?? '?'})`;
  }
  return `${user.name} (${user.id})`;
}
