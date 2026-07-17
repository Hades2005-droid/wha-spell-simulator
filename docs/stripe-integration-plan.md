# Stripe × Shadow Garden / wha-spell-simulator

**Status:** plan only (no live Stripe calls). Generated after Stripe MCP/plugin was unavailable in-session; grounded in Stripe docs skills (`stripe-best-practices`, API `2026-06-24.dahlia`).

**Secrets policy:** `env_only`. Never commit or print key values. Prefer restricted keys (`rk_`) over secret keys (`sk_`). Store real values in local `.env` / `~/ShadowGarden/.env` (`chmod 600`), never in packets, Gate files, or chat.

## Business context

| Surface | Role |
| --- | --- |
| wha-spell-simulator | Local-first Vite game + mesh tooling (Fable 5 / Phase 2 Black Sun) |
| Shadow Garden | Content-neutral orchestration mesh; Spacetime Alchemy engine |
| Monetization (future) | Optional commercial lanes — not required for Gate/symbolic play |

## Product map

| Stripe product | Use in this mesh | Primary API |
| --- | --- | --- |
| **Payments** | One-time unlocks / tips / pack purchases | Checkout Sessions (hosted or `ui_mode: 'custom'`) |
| **Billing** | Recurring “creator / lab seat” subscriptions | Billing + Checkout `mode: 'subscription'` + Customer Portal |
| **Connect** | Optional creator/agent payout lanes | Accounts **v2** (`/v2/core/accounts`) |
| **Invoicing** | B2B / studio invoices for mesh tooling | Invoices API + `automatic_tax` (after registrations) |
| **Tax** | Sales tax / VAT / GST on digital goods | Stripe Tax + Tax Registrations API |

## Architecture fit (important)

This repo is a **Vite SPA** (`npm run dev` → `127.0.0.1:5173`). There is **no** existing Node payment backend.

| Layer | Rule |
| --- | --- |
| Browser / Vite | Publishable key only (`STRIPE_PUBLISHABLE_KEY`). Never secret/RAK. |
| Local server | New small webhook + Checkout creator process (Node or Python), separate from game UI |
| Shadow Garden packet | Declare env **names** + `credentials_allowed: false` until an approved Gate opens provider calls |
| MCP router | Register Stripe as `payments` domain, `env_only`, approval-gated writes |

Recommended first backend shape (local-only):

```
tools/stripe_local/
  server.mjs          # Checkout + webhook (reads env)
  README.md           # runbook
src/adapters/stripeConfig.js   # env name resolution only (no keys in source)
```

Webhook endpoint shape:

```
POST /webhooks/stripe
Headers: Stripe-Signature
Verify with STRIPE_WEBHOOK_SECRET
Events (v1): checkout.session.completed, invoice.paid,
             customer.subscription.updated|deleted,
             account.updated (Connect capability)
```

Forward locally with Stripe CLI:

```bash
stripe listen --forward-to localhost:4242/webhooks/stripe
```

## Connect account model (creators / agents)

Treat creator/agent payouts as a **marketplace-style** lane until legal MoR is confirmed:

| Dimension | Choice | Why |
| --- | --- | --- |
| API | Accounts **v2** only | Do not use v1 `type: express|custom|standard` |
| Dashboard | `express` | Low-maintenance cobranded onboarding |
| Fees / losses | `application` | Platform owns pricing + negative-balance liability for destination charges |
| Charge pattern | Destination charges | Platform runs checkout; connected accounts receive transfers |
| Capabilities | `configuration.recipient` + `stripe_transfers` | Do not request merchant/card_payments for pure recipients |
| Fee take | `application_fee_amount` on Checkout/PaymentIntent | Not with separate charges+transfers |

If creators later “run their own store” (own customers), switch that lane to **SaaS / direct charges** (`dashboard: full`, `fees_collector/losses_collector: stripe`, merchant capabilities). Confirm MoR + tax liability with an advisor before enabling Tax on Connect.

## Checkout / Billing patterns

- Prefer Checkout Sessions; omit `payment_method_types` (dynamic methods).
- Tag sessions with `integration_identifier` (API ≥ `2026-03-25.dahlia`), e.g. `shadowgarden_checkout_<8rand>`.
- Subscriptions: Billing Prices (not deprecated Plans) + Customer Portal for self-serve.
- New usage-based mesh metering → prefer **Metronome**, not Billing Meters, for greenfield UBB.
- Invoicing: create Invoice → finalize → pay/send; enable Tax only after active registrations.

## Tax checklist (before `automatic_tax`)

1. Add Tax Registrations for obligated jurisdictions (Dashboard or Registrations API).
2. Set product tax codes from Stripe’s catalog (do not invent `txcd_`); pick a specific digital/SaaS code for US, not generic ESS by default.
3. Set `tax_behavior` on Prices.
4. Then `automatic_tax: { enabled: true }` on Checkout / Subscription / Invoice.
5. Without an active registration, Stripe silently collects **zero** tax.

## Env names (placeholders only)

```bash
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=rk_test_...          # prefer restricted key
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_API_VERSION=2026-06-24.dahlia
# Optional Connect / Tax
STRIPE_CONNECT_RETURN_URL=http://127.0.0.1:5173/billing/return
STRIPE_CONNECT_REFRESH_URL=http://127.0.0.1:5173/billing/refresh
STRIPE_TAX_ENABLED=false               # flip only after registrations exist
```

Also acceptable local-only mirror: `~/ShadowGarden/.env` with the same **names**.

## Shadow Garden packet / hooks posture

| Control | Recommendation until Gate opens |
| --- | --- |
| `credentials_allowed` | keep `false` |
| `provider_calls` | keep `false` for Stripe until approval |
| `content_neutral_base_build` | unchanged — payments are orthogonal to content |
| Packet lanes | add `stripe: local_env_only_manifest` (name only) when wiring |
| Hooks / MCP router | `draft_write` / `confirmed_write` require exact approval; no key values in ledger |

## Phased build order

1. **Auth + plugin** — `/add-plugin stripe`, reload session, connect MCP (`https://mcp.stripe.com`), run `stripe_implementation_planner`.
2. **Sandbox keys** — `stripe sandbox create` or Dashboard test keys → local `.env` only.
3. **Local webhook server** — Checkout Session create + signature-verified webhook.
4. **Billing** — one Product/Price + subscription Checkout + Customer Portal.
5. **Tax** — registrations → enable `automatic_tax`.
6. **Invoicing** — optional B2B path.
7. **Connect** — Accounts v2 recipient onboarding for creator lane (approval-gated).

## Explicit non-goals (Phase 2 Black Sun)

- No adult scrape / no content-gated unlocks in base build.
- No Stripe keys in `shadow_garden_packet.json`, Gate markdown, or agent transcripts.
- No embedding secret/RAK in Vite client bundles.

## Next commands (user)

```text
/add-plugin stripe
```

Then reload MCP tools or start a new agent chat, authenticate Stripe MCP when prompted, and re-run planning with `stripe_implementation_planner`.

Local fallback (already done once in this repo):

```bash
npx skills add https://docs.stripe.com
```
