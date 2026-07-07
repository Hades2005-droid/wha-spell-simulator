/**
 * Low-level Asana REST adapter.
 *
 * Thin wrapper over the Asana HTTP API. The `fetch` implementation is
 * injectable so tests can stub network calls; no live requests are made unless
 * a real fetch is provided. The Authorization header is built per-request and
 * never stored on the instance or logged.
 */

import { loadAsanaConfig } from './asanaConfig.js';

function resolveFetch(injected) {
  if (typeof injected === 'function') {
    return injected;
  }
  if (typeof globalThis !== 'undefined' && typeof globalThis.fetch === 'function') {
    return globalThis.fetch.bind(globalThis);
  }
  return null;
}

/**
 * Redact anything that looks like a bearer token from error messages so a
 * leaked token never reaches logs.
 */
function redact(message) {
  if (typeof message !== 'string') {
    return message;
  }
  return message.replace(/Bearer\s+[A-Za-z0-9._-]+/gi, 'Bearer [REDACTED]');
}

export class AsanaAdapter {
  /**
   * @param {object} [options]
   * @param {ReturnType<typeof loadAsanaConfig>} [options.config]
   * @param {typeof fetch} [options.fetch] Injectable fetch (required for live calls).
   */
  constructor(options = {}) {
    this.config = options.config ?? loadAsanaConfig();
    this.fetchImpl = resolveFetch(options.fetch);
  }

  isReady() {
    return Boolean(this.fetchImpl) && this.config.hasToken;
  }

  async request(method, path, body) {
    if (!this.fetchImpl) {
      throw new Error('AsanaAdapter: no fetch implementation available');
    }
    const token = this.config.getToken();
    if (!token) {
      throw new Error('AsanaAdapter: missing ASANA_ACCESS_TOKEN');
    }

    const url = `${this.config.apiBase}${path}`;
    const headers = {
      Authorization: `Bearer ${token}`,
      Accept: 'application/json',
    };
    const init = { method, headers };
    if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify({ data: body });
    }

    let response;
    try {
      response = await this.fetchImpl(url, init);
    } catch (error) {
      throw new Error(redact(`AsanaAdapter request failed: ${error.message}`));
    }

    const text = await response.text();
    let payload = null;
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch (error) {
        payload = { raw: text };
      }
    }

    if (!response.ok) {
      const detail = payload?.errors?.[0]?.message ?? `HTTP ${response.status}`;
      throw new Error(redact(`AsanaAdapter ${method} ${path} -> ${response.status}: ${detail}`));
    }

    return payload?.data ?? payload;
  }

  /** Post a comment (story) to a task. */
  addComment(taskId, text) {
    return this.request('POST', `/tasks/${encodeURIComponent(taskId)}/stories`, { text });
  }

  /** Update fields on a task (e.g. { notes, completed }). */
  updateTask(taskId, fields) {
    return this.request('PUT', `/tasks/${encodeURIComponent(taskId)}`, fields);
  }

  /** Create a task in a project. */
  createTask(projectId, fields) {
    return this.request('POST', '/tasks', { projects: [projectId], ...fields });
  }

  /** Lightweight identity probe used to validate credentials. */
  getMe() {
    return this.request('GET', '/users/me');
  }
}

export { redact as redactBearerTokens };
