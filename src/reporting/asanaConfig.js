/**
 * Asana Connector configuration.
 *
 * Reads settings from environment variables only. Tokens are NEVER hardcoded,
 * logged, or shipped in the browser bundle. This module is intended for
 * server/CLI use (Node). If it is imported in a browser context, token access
 * is refused so a Personal Access Token can never leak into a client bundle.
 */

const ASANA_API_BASE = 'https://app.asana.com/api/1.0';

// Environment variable names. Documented in docs/asana-connector.md.
const ENV = {
  token: 'ASANA_ACCESS_TOKEN',
  workspaceId: 'ASANA_WORKSPACE_ID',
  projectId: 'ASANA_PROJECT_SPELLSIM',
  taskId: 'ASANA_TASK_ID',
  enable: 'ASANA_REPORTING_ENABLED',
};

function isBrowserLike() {
  // Treat any environment exposing a DOM `window` as unsafe for token handling,
  // so a Personal Access Token can never be read from a browser bundle.
  return typeof globalThis !== 'undefined' && typeof globalThis.window !== 'undefined';
}

function readEnv(source) {
  if (source && typeof source === 'object') {
    return source;
  }
  if (typeof process !== 'undefined' && process.env) {
    return process.env;
  }
  return {};
}

/**
 * Build a sanitized, immutable config from environment variables.
 *
 * @param {Record<string, string>} [envSource] Optional env override (used in tests).
 * @returns {{
 *   apiBase: string,
 *   workspaceId: string|null,
 *   projectId: string|null,
 *   taskId: string|null,
 *   enabled: boolean,
 *   hasToken: boolean,
 *   getToken: () => string|null,
 * }}
 */
export function loadAsanaConfig(envSource) {
  const env = readEnv(envSource);
  const token = env[ENV.token] ? String(env[ENV.token]).trim() : '';
  const workspaceId = env[ENV.workspaceId] ? String(env[ENV.workspaceId]).trim() : null;
  const projectId = env[ENV.projectId] ? String(env[ENV.projectId]).trim() : null;
  const taskId = env[ENV.taskId] ? String(env[ENV.taskId]).trim() : null;

  // Reporting is opt-in. It only activates when explicitly enabled AND a token
  // plus a destination (project or task) is present.
  const explicitlyEnabled = String(env[ENV.enable] ?? '').toLowerCase() === 'true'
    || env[ENV.enable] === '1';
  const hasToken = token.length > 0;
  const hasDestination = Boolean(projectId || taskId);
  const enabled = explicitlyEnabled && hasToken && hasDestination;

  const browserUnsafe = isBrowserLike();

  return Object.freeze({
    apiBase: ASANA_API_BASE,
    workspaceId,
    projectId,
    taskId,
    enabled: enabled && !browserUnsafe,
    hasToken,
    // Token is only ever exposed through a function call, never as a property,
    // to reduce accidental serialization/logging. Refused in browser contexts.
    getToken() {
      if (browserUnsafe) {
        return null;
      }
      return hasToken ? token : null;
    },
  });
}

/**
 * Describe config for diagnostics/logging WITHOUT exposing the token.
 *
 * @param {ReturnType<typeof loadAsanaConfig>} config
 */
export function describeAsanaConfig(config) {
  return {
    apiBase: config.apiBase,
    workspaceId: config.workspaceId,
    projectId: config.projectId,
    taskId: config.taskId,
    enabled: config.enabled,
    tokenPresent: config.hasToken,
  };
}

export { ENV as ASANA_ENV_KEYS, ASANA_API_BASE };
