#!/usr/bin/env python3
"""demo.py — full offline Warrant x Crossmint flow, printed transcript.

Scenario: a user gives a shopping agent a $50 warrant; the agent delegates
$20 to a checkout sub-agent; the sub-agent buys a $12 item (approved -> a
scoped card is minted bounded by the warrant) and then attempts a $35 item
(denied OVER_BUDGET -> no card). A widening delegation is rejected outright.
Everything runs offline against the Crossmint stub: no API keys, no money.
"""

import time

from warrant import attenuate, issue_warrant, WarrantError
from crossmint_stub import CrossmintStub
from integration import request_scoped_card


def main() -> None:
    now = int(time.time())
    until = now + 3600  # one-hour mandate
    stub = CrossmintStub()

    print("== 1. User issues a $50 warrant to the shopping agent ==")
    w = issue_warrant({"agent_id": "shopper-1", "max_cents": 5000, "until": until})
    print(f"   authority: shopper-1, cap 5000c, until {until}")

    print("== 2. shopper-1 delegates $20 to the checkout sub-agent ==")
    w = attenuate(w, {"agent_id": "checkout-bot", "max_cents": 2000, "until": until})
    print("   hop: checkout-bot, cap 2000c (attenuated 5000 -> 2000)")

    print("== 3. checkout-bot buys a $12 item ==")
    r = request_scoped_card(stub, w, caller_agent_id="checkout-bot",
                            cost_cents=1200, description="IQBAR variety pack",
                            now=now)
    assert r["ok"] and r["card_issued"]
    print(f"   APPROVED -> order intent {r['intent']['id']}: "
          f"amount={r['intent']['amount_cents']}c expires={r['intent']['expires_at']}")
    print(f"   scoped card {r['card']['id']}: spend_limit={r['card']['spend_limit_cents']}c "
          f"expires={r['card']['expires_at']}")
    s = stub.spend(r["card"]["id"], 1200, now=now)
    print(f"   card spend 1200c: {s}")

    print("== 4. checkout-bot attempts a $35 item ==")
    r = request_scoped_card(stub, w, caller_agent_id="checkout-bot",
                            cost_cents=3500, description="headphones", now=now)
    assert not r["ok"] and not r["card_issued"]
    print(f"   DENIED ({r['code']}): {r['detail']} -> no card minted")

    print("== 5. widening attempt: delegate $60 out of a $50 warrant ==")
    try:
        attenuate(w, {"agent_id": "checkout-bot", "max_cents": 6000, "until": until})
        print("   ERROR: widening was allowed (bug)")
    except WarrantError as e:
        print(f"   REJECTED: {e} -> delegation chain stays attenuated")

    print("\nDone. The warrant decided; Crossmint's rail only issued what it allowed.")


if __name__ == "__main__":
    main()
