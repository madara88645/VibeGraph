import { buildUserPayload } from './utils.js';

/**
 * Async fetch — central entry for remote user data in this demo graph.
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
