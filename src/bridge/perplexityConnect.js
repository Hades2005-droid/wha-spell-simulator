/**
 * Perplexity auto-connect helpers for mesh / oracle work going forward.
 * Env names only in manifests; never returns secret values.
 */

const ENV_NAMES = [
  'PERPLEXITY_API_KEY',
  'PPLX_API_KEY',
  'PERPLEXITY_BASE_URL',
  'PERPLEXITY_MODEL',
  'ENABLE_PERPLEXITY',
  'PERPLEXITY_LIVE_OK',
];

const CONNECT_CLI = 'tools/perplexity_connect.py';
const CENTRAL_CLI = 'tools/perplexity_asuna_central_control.py';

function envPresence() {
  const out = {};
  for (const name of ENV_NAMES) {
    out[name] = Boolean(process.env[name]);
  }
  return out;
}

export function perplexityKeyPresent() {
  return Boolean(process.env.PERPLEXITY_API_KEY || process.env.PPLX_API_KEY);
}

/**
 * Manifest used when agents should auto-leverage Perplexity for research.
 */
export function getPerplexityConnectStatus() {
  const keyPresent = perplexityKeyPresent();
  return {
    schema: 'shadow_garden.perplexity_connect_status.v1',
    role: 'auto_connect_research',
    ok: keyPresent,
    apiKeyPresent: keyPresent,
    baseUrl: process.env.PERPLEXITY_BASE_URL || 'https://api.perplexity.ai',
    defaultModel: process.env.PERPLEXITY_MODEL || 'sonar-pro',
    connectCli: CONNECT_CLI,
    centralControlCli: CENTRAL_CLI,
    envPresent: envPresence(),
    autoConnectFor: [
      'polymarket_api_research',
      'entropy_oracle_hardening',
      'discord_status_notify_metadata',
    ],
    controls: {
      secretLogging: false,
      bulkUploadRequiresApproval: true,
      contentNeutral: true,
    },
    hint: keyPresent
      ? `python3 ${CONNECT_CLI} health`
      : 'Set PERPLEXITY_API_KEY for auto-connect (never commit).',
  };
}

export default {
  getPerplexityConnectStatus,
  perplexityKeyPresent,
};
