# OUTREACH DRAFT — DO NOT SEND

Status: draft only. Not sent. Awaiting Corey Tasz's explicit approval
of the exact content and the exact recipient before anything goes out.

## Verified recipient options (do not guess others)

- **support@crossmint.com** — entity contact listed in Crossmint's own
  Terms of Service (Crossmint, Inc., 1317 Edgewater Dr #4296, Orlando, FL 32804).
- **https://www.crossmint.com/contact/sales** — sales/partnership contact form,
  cited verbatim in Crossmint's own press releases ("contact the team at
  https://www.crossmint.com/contact/sales").
- press@crossmint.com exists (Brett Li, Head of Marketing) but is media-only —
  not appropriate for a partnership pitch.

No verified partnerships@ address was found; do not invent one.

## Draft email

**To:** support@crossmint.com
**Subject:** Warrant: an open delegation layer for the Agent Commerce Toolkit

Hi Crossmint team,

I'm Corey Tasz, solo founder of Slid Phi Labs. Your Agent Commerce
Toolkit launch caught my eye — scoped virtual cards with spend limits and
expirations are exactly the right shape for agent payments.

I've built the other half of that shape and I'd like to talk about
integrating it. It's called Warrant: a signed, portable spend mandate that
attenuates as it delegates. A user issues an agent a $50 mandate; the agent
hands a sub-agent $20 of it; the sub-agent mathematically cannot widen it
back to $60. Verification is offline, deny-by-default, and the mandate's
cap and expiry map 1:1 onto your order-intent model — amount and expiration
derive from the signed warrant instead of being set by the app.

The pitch in one line: Crossmint issues the card, Warrant decides what it's
allowed to do.

I've put together a working offline demo of the full flow — warrant
issuance, attenuated delegation, approved purchase minting a scoped card
bounded by the mandate, over-budget purchase denied with nothing minted —
plus a writeup of the integration shape (warrant → order intent
translation, delegation chains recorded on intents for auditability,
attenuated sub-cards without fresh approval round-trips). Happy to share
the repo and walk through it.

Would a 20-minute call this week or next work?

Best,
Corey Tasz
Slid Phi Labs
slidphilabs.com
