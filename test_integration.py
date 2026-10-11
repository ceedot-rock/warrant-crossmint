#!/usr/bin/env python3
"""test_integration.py — the demo's claims, as tests.

Run:  python3 test_integration.py
"""

import time
import unittest

from warrant import (WarrantError, attenuate, gate_check, issue_warrant,
                     verify_warrant)
from crossmint_stub import CrossmintStub
from integration import request_scoped_card, warrant_to_order_intent

NOW = 1_800_000_000
UNTIL = NOW + 3600


def fresh():
    w = issue_warrant({"agent_id": "shopper-1", "max_cents": 5000, "until": UNTIL})
    return attenuate(w, {"agent_id": "checkout-bot", "max_cents": 2000, "until": UNTIL})


class TestWarrantCrossmint(unittest.TestCase):
    def test_attenuation_across_hops(self):
        w = fresh()
        v = verify_warrant(w, NOW)
        self.assertTrue(v["ok"])
        self.assertEqual(v["body"]["agent_id"], "checkout-bot")
        self.assertEqual(v["body"]["max_cents"], 2000)  # 5000 -> 2000

    def test_widening_rejected(self):
        w = fresh()
        with self.assertRaises(WarrantError) as cm:
            attenuate(w, {"agent_id": "checkout-bot", "max_cents": 6000, "until": UNTIL})
        self.assertEqual(str(cm.exception), "warrant_widen_cents")
        with self.assertRaises(WarrantError) as cm2:
            attenuate(w, {"agent_id": "checkout-bot", "max_cents": 2000,
                          "until": UNTIL + 3600})
        self.assertEqual(str(cm2.exception), "warrant_widen_until")

    def test_over_budget_denied_no_card(self):
        stub = CrossmintStub()
        r = request_scoped_card(stub, fresh(), caller_agent_id="checkout-bot",
                                cost_cents=3500, description="headphones", now=NOW)
        self.assertFalse(r["ok"])
        self.assertEqual(r["code"], "OVER_BUDGET")
        self.assertFalse(r["card_issued"])
        self.assertEqual(len(stub.cards), 0)  # nothing minted on denial

    def test_approved_maps_to_card_params(self):
        stub = CrossmintStub()
        r = request_scoped_card(stub, fresh(), caller_agent_id="checkout-bot",
                                cost_cents=1200, description="IQBAR variety pack",
                                merchant="iqbar.com", now=NOW)
        self.assertTrue(r["ok"])
        self.assertTrue(r["card_issued"])
        # The order intent carries the EFFECTIVE (attenuated) cap and expiry:
        self.assertEqual(r["intent"]["amount_cents"], 2000)
        self.assertEqual(r["intent"]["expires_at"], UNTIL)
        self.assertEqual(r["intent"]["merchant"], "iqbar.com")
        # The scoped card is bounded by the intent, exactly:
        self.assertEqual(r["card"]["spend_limit_cents"], r["intent"]["amount_cents"])
        self.assertEqual(r["card"]["expires_at"], r["intent"]["expires_at"])
        # And the card enforces it at spend time:
        self.assertTrue(stub.spend(r["card"]["id"], 1200, now=NOW)["ok"])
        self.assertEqual(stub.spend(r["card"]["id"], 900, now=NOW)["code"], "OVER_LIMIT")

    def test_expired_warrant_denied(self):
        stub = CrossmintStub()
        r = request_scoped_card(stub, fresh(), caller_agent_id="checkout-bot",
                                cost_cents=100, description="x", now=UNTIL + 1)
        self.assertFalse(r["ok"])
        self.assertEqual(r["code"], "WARRANT_EXPIRED")
        self.assertFalse(r["card_issued"])

    def test_agent_mismatch_denied(self):
        stub = CrossmintStub()
        r = request_scoped_card(stub, fresh(), caller_agent_id="shopper-1",
                                cost_cents=100, description="x", now=NOW)
        self.assertFalse(r["ok"])
        self.assertEqual(r["code"], "AGENT_MISMATCH")
        self.assertFalse(r["card_issued"])

    def test_intent_translation_uses_effective_cap(self):
        params = warrant_to_order_intent(fresh(), description="t", now=NOW)
        self.assertEqual(params["amount_cents"], 2000)
        self.assertEqual(params["expires_at"], UNTIL)
        self.assertEqual(params["agent_id"], "checkout-bot")

    def test_invalid_warrant_raises_on_translate(self):
        with self.assertRaises(WarrantError):
            warrant_to_order_intent({"kind": "bogus"}, description="t", now=NOW)


if __name__ == "__main__":
    unittest.main(verbosity=2)
