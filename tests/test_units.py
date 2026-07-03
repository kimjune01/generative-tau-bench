"""Unit tests for the parser and paired-comparison fixes (pure, no API)."""
from __future__ import annotations

from gtau.adapters.base import parse_action
from gtau.metrics import mcnemar, pass_hat_k, pass_at_k


def test_parse_picks_last_action_over_echoed_schema():
    # agent echoes a tool schema (has "name") then emits its real action last
    out = (
        'thinking... here is a schema {"type":"function","function":{"name":"x"}}\n'
        'my action: {"tool": "get_order_details", "arguments": {"order_id": "#W1"}}'
    )
    a = parse_action(out)
    assert a.name == "get_order_details" and a.kwargs == {"order_id": "#W1"}


def test_parse_respond():
    a = parse_action('{"respond": "Could you share your zip code?"}')
    assert a.name == "respond" and a.kwargs == {"content": "Could you share your zip code?"}


def test_parse_stop_and_missing():
    assert parse_action('done {"stop": true}').name == "stop"
    try:
        parse_action("no json here")
        assert False, "should have raised"
    except ValueError:
        pass


def test_mcnemar_agreement_and_asymmetry():
    both = [True, True, False, False]
    assert mcnemar(both, both)["p_value"] == 1.0  # no discordant pairs
    a = [True] * 10 + [False] * 0
    b = [False] * 10
    r = mcnemar(a, b)  # a wins all 10 discordant
    assert r["a_only"] == 10 and r["b_only"] == 0
    assert 0.0 <= r["p_value"] <= 0.01  # strongly significant


def test_pass_hat_k_monotone():
    spt = {0: 6, 1: 8}  # successes out of n
    assert pass_hat_k(spt, 8, 1) >= pass_hat_k(spt, 8, 8)      # pass^k falls with k
    assert pass_at_k(spt, 8, 8) >= pass_at_k(spt, 8, 1)        # pass@k rises with k
