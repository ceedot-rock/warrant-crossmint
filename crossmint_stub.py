#!/usr/bin/env python3
"""
crossmint_stub.py — OFFLINE STUB of Crossmint's order-intent / scoped-card model.

Mirrors the documented model (docs.crossmint.com "How Agents Pay"): the user
saves a card in Crossmint's PCI vault; the app creates *order intents* — an
allowance with an amount, a description, an expiration, and optionally a
merchant. The user approves each intent and can cancel it anytime. From an
active intent the agent mints credentials bounded by the allowance (Visa
Intelligent Commerce / Mastercard Agent Pay scoped virtual cards, network
tokens, etc.). The real card number never leaves the vault.

This stub reproduces the *decision surface* (bounds checked at issuance and
at spend) with no network, no API keys, and no real money. It exists so the
Warrant -> Crossmint mapping can be demonstrated and tested offline.
"""

from __future__ import annotations

from typing import Optional


class CrossmintStub:
    def __init__(self) -> None:
        self.intents: dict[str, dict] = {}
        self.cards: dict[str, dict] = {}
        self._seq = 0

    # -- order intents -----------------------------------------------------
    def create_order_intent(self, *, amount_cents: int, description: str,
                            expires_at: int, agent_id: str,
                            merchant: Optional[str] = None) -> dict:
        """Create an approved order intent (allowance)."""
        if not isinstance(amount_cents, int) or amount_cents < 0:
            raise ValueError("amount_cents must be a non-negative int")
        if not isinstance(expires_at, int) or expires_at <= 0:
            raise ValueError("expires_at must be a positive unix timestamp")
        if not agent_id:
            raise ValueError("agent_id is required")
        self._seq += 1
        intent_id = f"oi_{self._seq:06d}"
        intent = {
            "id": intent_id,
            "amount_cents": amount_cents,
            "description": description,
            "expires_at": expires_at,
            "agent_id": agent_id,
            "merchant": merchant,
            "status": "approved",   # user approved; the stub models the approved path
            "spent_cents": 0,
            "cancelled": False,
        }
        self.intents[intent_id] = intent
        return intent

    def cancel_order_intent(self, intent_id: str) -> None:
        self.intents[intent_id]["cancelled"] = True

    # -- scoped card issuance ----------------------------------------------
    def mint_scoped_card(self, intent_id: str) -> dict:
        """Mint a scoped virtual card bounded by the intent's allowance."""
        intent = self.intents[intent_id]
        if intent["cancelled"] or intent["status"] != "approved":
            raise ValueError("cannot mint: intent not active")
        card_id = f"card_{intent_id}"
        card = {
            "id": card_id,
            "intent_id": intent_id,
            "spend_limit_cents": intent["amount_cents"],  # bounded by the allowance
            "expires_at": intent["expires_at"],
        }
        self.cards[card_id] = card
        return card

    # -- spend ----------------------------------------------------------------
    def spend(self, card_id: str, amount_cents: int, *, now: int) -> dict:
        """Charge against a scoped card. Returns {"ok": ...} — never raises."""
        card = self.cards.get(card_id)
        if card is None:
            return {"ok": False, "code": "CARD_UNKNOWN"}
        intent = self.intents[card["intent_id"]]
        if intent["cancelled"] or intent["status"] != "approved":
            return {"ok": False, "code": "INTENT_REVOKED"}
        if now >= card["expires_at"]:
            return {"ok": False, "code": "CARD_EXPIRED"}
        if amount_cents > card["spend_limit_cents"] - intent["spent_cents"]:
            return {"ok": False, "code": "OVER_LIMIT"}
        intent["spent_cents"] += amount_cents
        return {"ok": True,
                "remaining_cents": card["spend_limit_cents"] - intent["spent_cents"]}
