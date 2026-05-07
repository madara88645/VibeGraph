import { buildUserPayload } from './utils.js';

/**
 * Fetches remote user JSON for the dashboard.
 * Async boundary demonstrates promise-based cross-file flow.
 */
export async function fetchUserData(userId) {
  const payload = buildUserPayload(userId);
  const url = `https://jsonplaceholder.typicode.com/users/${payload.id}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`fetchUserData failed: ${response.status}`);
  }
  return response.json();
}
