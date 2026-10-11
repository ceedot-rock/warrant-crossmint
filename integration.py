#!/usr/bin/env python3
"""
integration.py — Warrant x Crossmint: the bridge.

Thesis: Crossmint issues the card, Warrant decides what it's allowed to do.

The mapping (verified against Crossmint's documented order-intent model):
  warrant effective max_cents  ->  order intent amount (the allowance)
  warrant effective until      ->  order intent expiration
  warrant effective agent_id   ->  the agent the intent is bound to
  delegation hop               ->  attenuated child order intent
                                  (Crossmint has no native delegation chains;
                                   Warrant adds them)
  merchant                     ->  Crossmint-side field; Warrant is spend-scoped
                                  only and does not speak merchant allow-lists.
                                  Honest boundary, stated in the writeup.

Flow: the Warrant gate runs FIRST, deny-by-default. Only an approved gate
decision produces an order intent + scoped card. A denied decision produces
no issuance at all — the mapping of decisions to card parameters is the
whole integration.
"""

from __future__ import annotations

from typing import Optional

from warrant import WarrantError, gate_check, verify_warrant
from crossmint_stub import CrossmintStub


def warrant_to_order_intent(warrant: dict, *, description: str,
                            merchant: Optional[str] = None,
                            now: Optional[int] = None) -> dict:
    """Translate a verified warrant into Crossmint order-intent parameters.

    Uses the EFFECTIVE (last-hop) body, so delegation attenuation is
    reflected in the issued allowance. Raises WarrantError on an
    invalid or expired warrant.
    """
    v = verify_warrant(warrant, now)
    if not v["ok"]:
        raise WarrantError(v["error"])
    body = v["body"]
    return {
        "amount_cents": body["max_cents"],
        "description": description,
        "expires_at": body["until"],
        "agent_id": body["agent_id"],
        "merchant": merchant,
    }


def request_scoped_card(stub: CrossmintStub, warrant: dict, *,
                        caller_agent_id: str, cost_cents: int,
                        description: str, merchant: Optional[str] = None,
                        now: Optional[int] = None) -> dict:
    """Full flow: Warrant gate first, Crossmint issuance only on approval.

    Returns {"ok": True, "card": ..., "intent": ..., "card_issued": True}
    or      {"ok": False, "code": ..., "detail": ..., "card_issued": False}.
    """
    gate = gate_check(warrant, caller_agent_id, cost_cents, now)
    if not gate["ok"]:
        # Denied: nothing is minted. The decision maps to "no card".
        return {"ok": False, "code": gate["code"], "detail": gate["detail"],
                "card_issued": False}
    params = warrant_to_order_intent(warrant, description=description,
                                     merchant=merchant, now=now)
    intent = stub.create_order_intent(**params)
    card = stub.mint_scoped_card(intent["id"])
    return {"ok": True, "card": card, "intent": intent, "card_issued": True}
