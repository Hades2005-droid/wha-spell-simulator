#!/usr/bin/env node
/**
 * Shadow Garden local Stripe scaffold (Payments / Billing / webhooks).
 *
 * Default: dry-run / status only — no live Stripe SDK calls unless
 * STRIPE_LIVE_OK=1 and STRIPE_SECRET_KEY are set.
 *
 * Env names only in logs. Never print key values.
 */
import http from 'node:http';
import { createHmac, timingSafeEqual } from 'node:crypto';

const PORT = Number(process.env.STRIPE_LOCAL_PORT || 4242);
const LIVE = process.env.STRIPE_LIVE_OK === '1';
const SECRET = process.env.STRIPE_SECRET_KEY || '';
const WEBHOOK_SECRET = process.env.STRIPE_WEBHOOK_SECRET || '';
const PUBLISHABLE = process.env.STRIPE_PUBLISHABLE_KEY || '';
const API_VERSION = process.env.STRIPE_API_VERSION || '2026-06-24.dahlia';

function presence() {
  return {
    STRIPE_PUBLISHABLE_KEY: Boolean(PUBLISHABLE),
    STRIPE_SECRET_KEY: Boolean(SECRET),
    STRIPE_WEBHOOK_SECRET: Boolean(WEBHOOK_SECRET),
    STRIPE_LIVE_OK: LIVE,
  };
}

function json(res, status, body) {
  const payload = JSON.stringify(body, null, 2);
  res.writeHead(status, {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-store',
  });
  res.end(payload);
}

function verifyStripeSignature(rawBody, header, secret) {
  if (!header || !secret) return false;
  // Stripe-Signature: t=timestamp,v1=sig
  const parts = Object.fromEntries(
    header.split(',').map((p) => {
      const [k, v] = p.trim().split('=');
      return [k, v];
    }),
  );
  const t = parts.t;
  const v1 = parts.v1;
  if (!t || !v1) return false;
  const signed = `${t}.${rawBody}`;
  const expected = createHmac('sha256', secret).update(signed, 'utf8').digest('hex');
  try {
    const a = Buffer.from(expected, 'hex');
    const b = Buffer.from(v1, 'hex');
    return a.length === b.length && timingSafeEqual(a, b);
  } catch {
    return false;
  }
}

async function readRaw(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  return Buffer.concat(chunks).toString('utf8');
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url || '/', `http://127.0.0.1:${PORT}`);

  if (req.method === 'GET' && url.pathname === '/health') {
    return json(res, 200, {
      ok: true,
      service: 'shadow_garden_stripe_local',
      bind: '127.0.0.1',
      port: PORT,
      live: LIVE,
      env_present: presence(),
      api_version: API_VERSION,
      products: ['Payments', 'Billing', 'Connect', 'Invoicing', 'Tax'],
      mode: LIVE && SECRET ? 'armed_live_keys_present' : 'dry_run',
      controls: {
        secret_logged: false,
        content_neutral: true,
        live_requires_STRIPE_LIVE_OK: true,
      },
    });
  }

  if (req.method === 'GET' && url.pathname === '/v1/manifest') {
    return json(res, 200, {
      schema: 'shadow_garden.stripe_local_manifest.v1',
      checkout: {
        mode_one_time: 'payment',
        mode_subscription: 'subscription',
        omit_payment_method_types: true,
        integration_identifier_prefix: 'shadowgarden_checkout_',
      },
      connect: {
        api: 'accounts_v2',
        dashboard: 'express',
        charge_pattern: 'destination',
        note: 'No v1 type=express; use /v2/core/accounts',
      },
      tax: {
        automatic_tax: process.env.STRIPE_TAX_ENABLED === 'true',
        requires_registrations: true,
      },
      webhook_path: '/webhooks/stripe',
      env_names: Object.keys(presence()),
      live: LIVE,
    });
  }

  if (req.method === 'POST' && url.pathname === '/v1/checkout/session') {
    if (!LIVE || !SECRET) {
      return json(res, 200, {
        ok: true,
        dry_run: true,
        message:
          'Checkout Session not created (dry-run). Set STRIPE_LIVE_OK=1 and STRIPE_SECRET_KEY to arm.',
        would_create: {
          mode: 'payment_or_subscription',
          success_url: 'http://127.0.0.1:5173/billing/success',
          cancel_url: 'http://127.0.0.1:5173/billing/cancel',
        },
      });
    }
    return json(res, 501, {
      ok: false,
      error: 'live_checkout_not_wired_install_stripe_sdk',
      hint: 'npm i stripe && wire createCheckoutSession — MCP planner preferred after /add-plugin stripe',
    });
  }

  if (req.method === 'POST' && url.pathname === '/webhooks/stripe') {
    const raw = await readRaw(req);
    const sig = req.headers['stripe-signature'];
    const verified = WEBHOOK_SECRET
      ? verifyStripeSignature(raw, String(sig || ''), WEBHOOK_SECRET)
      : false;
    if (WEBHOOK_SECRET && !verified) {
      return json(res, 400, { ok: false, error: 'invalid_signature' });
    }
    let eventType = 'unknown';
    try {
      eventType = JSON.parse(raw).type || eventType;
    } catch {
      /* ignore */
    }
    return json(res, 200, {
      ok: true,
      received: true,
      verified: Boolean(WEBHOOK_SECRET) && verified,
      dry_run: !LIVE,
      event_type: eventType,
      note: 'Handler acknowledges only — no business mutation in scaffold',
    });
  }

  return json(res, 404, { ok: false, error: 'not_found' });
});

server.listen(PORT, '127.0.0.1', () => {
  // eslint-disable-next-line no-console
  console.log(
    JSON.stringify({
      service: 'shadow_garden_stripe_local',
      listening: `http://127.0.0.1:${PORT}`,
      live: LIVE,
      env_present: presence(),
    }),
  );
});
