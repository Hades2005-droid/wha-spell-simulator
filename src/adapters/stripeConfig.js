/**
 * Stripe env-name resolver for Shadow Garden / Vite.
 * Never imports or embeds secret/RAK values — publishable key only in browser.
 */
const ENV = typeof process !== 'undefined' && process.env ? process.env : {};

export const STRIPE_ENV_NAMES = Object.freeze([
  'STRIPE_PUBLISHABLE_KEY',
  'STRIPE_SECRET_KEY',
  'STRIPE_WEBHOOK_SECRET',
  'STRIPE_API_VERSION',
  'STRIPE_CONNECT_RETURN_URL',
  'STRIPE_CONNECT_REFRESH_URL',
  'STRIPE_TAX_ENABLED',
  'STRIPE_LOCAL_PORT',
]);

export function stripePublishableKey() {
  const key = ENV.STRIPE_PUBLISHABLE_KEY || ENV.VITE_STRIPE_PUBLISHABLE_KEY || '';
  if (key && !key.startsWith('pk_')) {
    throw new Error('STRIPE_PUBLISHABLE_KEY must start with pk_');
  }
  return key || null;
}

export function stripeConfigManifest() {
  return {
    schema: 'shadow_garden.stripe_config_manifest.v1',
    env_names: [...STRIPE_ENV_NAMES],
    publishable_present: Boolean(ENV.STRIPE_PUBLISHABLE_KEY || ENV.VITE_STRIPE_PUBLISHABLE_KEY),
    secret_present: Boolean(ENV.STRIPE_SECRET_KEY),
    webhook_secret_present: Boolean(ENV.STRIPE_WEBHOOK_SECRET),
    api_version: ENV.STRIPE_API_VERSION || '2026-06-24.dahlia',
    tax_enabled_flag: String(ENV.STRIPE_TAX_ENABLED || 'false').toLowerCase() === 'true',
    local_port: Number(ENV.STRIPE_LOCAL_PORT || 4242),
    controls: {
      credentials_in_source: false,
      secret_in_browser: false,
      live_charges_require_approval: true,
      content_neutral: true,
    },
  };
}

export default {
  STRIPE_ENV_NAMES,
  stripePublishableKey,
  stripeConfigManifest,
};
