/**
 * Access-token storage.
 *
 * The token lives in a module-scoped variable, not in localStorage or
 * sessionStorage. Anything in web storage is readable by any script that runs
 * on the page, so a single XSS payload would be enough to lift a session. A
 * module variable dies with the tab; the refresh cookie (httpOnly) is what
 * restores the session on reload, and JavaScript cannot read it at all.
 */

let accessToken: string | null = null;
const listeners = new Set<(token: string | null) => void>();

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
  listeners.forEach((listener) => listener(token));
}

export function clearAccessToken(): void {
  setAccessToken(null);
}

export function onTokenChange(listener: (token: string | null) => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
