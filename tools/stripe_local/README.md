# Shadow Garden — local Stripe scaffold

Bind: `127.0.0.1` only. Secrets: env names in `.env` / `~/ShadowGarden/.env` (`chmod 600`).

## Run (dry-run default)

```bash
cd ~/wha-spell-simulator
node tools/stripe_local/server.mjs
# GET http://127.0.0.1:4242/health
# GET http://127.0.0.1:4242/v1/manifest
```

Arm live keys only after approval:

```bash
export STRIPE_LIVE_OK=1
# STRIPE_SECRET_KEY / STRIPE_PUBLISHABLE_KEY / STRIPE_WEBHOOK_SECRET already in env
node tools/stripe_local/server.mjs
```

Forward webhooks:

```bash
stripe listen --forward-to localhost:4242/webhooks/stripe
```

## Products covered (scaffolded)

Payments, Billing, Connect (Accounts v2 notes), Invoicing, Tax — see `docs/stripe-integration-plan.md`.

Checkout create stays dry-run until Stripe SDK + MCP planner (`/add-plugin stripe`) complete the live path.
