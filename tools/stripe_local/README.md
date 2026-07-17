# Shadow Garden — local Stripe scaffold

Bind: `127.0.0.1` only. Secrets: env names in local env files (`chmod 600`). Never commit values.

## Run (dry-run default)

```bash
npm run stripe:local
# GET http://127.0.0.1:4242/health
# GET http://127.0.0.1:4242/v1/manifest
# POST http://127.0.0.1:4242/v1/checkout/session  {"amount_cents":500}
```

## Arm live / sandbox Checkout Sessions

1. Create sandbox keys (no Dashboard account required for trial):

```bash
npm run stripe:sandbox
# copy the printed publishable + restricted/secret names into your shell env
```

2. Or paste restricted keys from Dashboard into shell env (prefer `rk_test_…`).

3. Start armed:

```bash
export STRIPE_LIVE_OK=1
# also set publishable, secret, and webhook signing names in the environment
npm run stripe:local
curl -s -X POST http://127.0.0.1:4242/v1/checkout/session \
  -H 'content-type: application/json' \
  -d '{"amount_cents":500,"product_name":"Shadow Garden session"}'
```

Forward webhooks:

```bash
npx --yes @stripe/cli listen --forward-to localhost:4242/webhooks/stripe
```

## Products covered

Payments (Checkout Sessions), Billing, Connect (Accounts v2 notes), Invoicing, Tax — see `docs/stripe-integration-plan.md`.

Rules enforced in scaffold: omit `payment_method_types`; `integration_identifier` on create; Tax off until registrations exist.
