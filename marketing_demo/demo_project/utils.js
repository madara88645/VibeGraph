/** Shared helpers for API + UI layers. */

export function buildUserPayload(userId) {
  return { id: String(userId).trim() };
}

export function formatDisplayName(user) {
  if (!user?.name) {
    return `anonymous (${user?.id ?? '?'})`;
  }
  return `${user.name} (${user.id})`;
}
