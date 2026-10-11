# Warrant × Crossmint

**Crossmint issues the card. Warrant decides what it's allowed to do.**

Crossmint's [Agent Commerce Toolkit](https://www.prnewswire.com/news-releases/crossmint-launches-agent-commerce-toolkit-enabling-ai-agents-to-pay-with-any-card-and-check-out-online-through-one-integration-302901649.html) (Oct 2026) gives agents a single integration for payments: the user saves a card in Crossmint's PCI vault, the app creates **order intents** — an allowance with an amount, a description, an expiration, and optionally a merchant — the user approves each one, and from an active intent the agent mints scoped credentials (Visa Intelligent Commerce / Mastercard Agent Pay virtual cards, network tokens). The bound is enforced outside the agent. ([How Agents Pay — Crossmint docs](http://docs.crossmint.com/agents/how-agents-pay))

Warrant (Slid Phi Labs) is the missing half: a **portable, offline-verifiable delegation layer**. A Warrant is a signed spend mandate — `{v:1, kind:"spl-narrow", authority:{agent_id,max_cents,until}, hops:[...]}` — where each delegation hop may only *shrink* the cap and may never extend the expiry. Deny-by-default enforcement. No network required to verify.

## The mapping

| Warrant | Crossmint order intent |
|---|---|
| effective `max_cents` (last hop) | intent `amount` (the allowance) |
| effective `until` | intent `expiration` |
| effective `agent_id` | the agent the intent is bound to |
| delegation hop | attenuated child order intent |
| — | `merchant` |

What Warrant adds that Crossmint's model doesn't have natively:

1. **Delegation chains.** Crossmint's intents are user→agent allowances. Warrant lets an agent *re-delegate* a narrowed slice of its own mandate to a sub-agent — offline, verifiable, mathematically unable to widen.
2. **Deny-by-default policy before issuance.** The Warrant gate runs first. An `OVER_BUDGET` / `WARRANT_EXPIRED` / `AGENT_MISMATCH` decision means *no card is minted at all*. The decision maps directly to issuance parameters: approved → intent amount = effective cap; denied → nothing.
3. **Portability.** A Warrant is a signed JSON object. It travels with the agent across rails (x402, MPP, card networks) and the same mandate can mint correctly-scoped credentials on each.

Honest boundary: Warrant is spend-scoped only. Merchant allow-lists, PCI vaulting, network enforcement, and user approval UX all stay Crossmint-side. Warrant is the authorization policy; Crossmint is the issuance and enforcement rail.

## What this repo proves (offline, no API keys)

- `warrant.py` — the narrow Warrant: issue, attenuate (never widen), verify, deny-by-default gate. Exact error strings.
- `crossmint_stub.py` — offline model of Crossmint's order-intent + scoped-card surface: intents with amount/expiration/merchant, card minting bounded by the intent, spend-time bound checks, revocation.
- `integration.py` — the bridge. `warrant_to_order_intent()` translates the effective warrant body into intent parameters; `request_scoped_card()` runs the Warrant gate first and only mints on approval.
- `demo.py` — `$50` warrant → `$20` delegation → `$12` purchase approved (scoped card minted, limit = 2000¢, expiry = warrant `until`) → `$35` purchase denied `OVER_BUDGET` (no card) → `$60` widening delegation rejected.
- `test_integration.py` — 8 tests, all passing: attenuation across hops, widening rejection (cents + until), over-budget denial with zero cards minted, approved-decision → card param mapping, expiry denial, agent mismatch, effective-cap translation.

Run it:

```
python3 test_integration.py   # 8 tests, stdlib only
python3 demo.py               # printed transcript of the full flow
```

## Proposed integration shape (for the conversation with Crossmint)

1. Accept a signed Warrant as an input to order-intent creation: `amount` and `expiration` derive from the warrant's effective body instead of being set by the app.
2. Record the warrant's delegation chain on the intent, so auditors see *why* the allowance is what it is.
3. Let agents holding attenuated warrants mint their own scoped sub-cards without a fresh user approval round-trip — the user's original approval covers every narrowed hop by construction.

Nothing here touches real money or real card rails. The stub is a stand-in for Crossmint's API; swapping it for real calls is mechanical once there's a partnership conversation.
