"""Seeded re-keying of a retail instance.

The load-bearing move of generative tau-bench: because the oracle is computed by
*replaying* a golden action program (not by reading a stored answer), we can alpha-
rename an instance and the oracle re-derives for free. This module builds a seeded
bijection over the id namespaces of the retail world and applies it consistently to
the database, the golden action program, and any text (instruction, outputs).

Re-keying is a faithful alpha-rename of the *initial DB and the golden program*.
It does NOT commute with replay in general: some tools order lists by id value
(e.g. `exchange` stores `sorted(new_item_ids)`), so re-keying can change a sort
order, and `rekey(replay(golden, db)) != replay(rekey(golden), rekey(db))`. That is
fine: the oracle we grade against is `replay(rekey(golden), rekey(db))`, which is
self-consistent, because the agent under test sorts the same re-keyed ids the same
way. The properties we actually require (see tests/test_rekey_invariance.py) are:
coverage (no original id leaks through), injectivity, and clean solvability (the
re-keyed golden replays on the re-keyed DB with no tool errors).

This is cosmetic re-keying (relabel ids/values), which defeats verbatim
memorization. Structural regeneration (resampling contents under task constraints)
is a separate, class-aware layer; see DESIGN.md.

No tau_bench import here: pure dict/list/str transforms.
"""
from __future__ import annotations
import random
import string
from typing import Any, Dict, List, Tuple

from .action import Action

# ---- id space collectors -----------------------------------------------------
# Each namespace: how to find every existing id in the DB, and how to mint a fresh
# one deterministically from the RNG. Fresh ids are drawn without replacement so
# the map is injective within a namespace.


def _digits(rng: random.Random, n: int) -> str:
    return "".join(rng.choice(string.digits) for _ in range(n))


def _collect(data: Dict[str, Any]) -> Dict[str, set]:
    users, orders, products = data["users"], data["orders"], data["products"]
    item_ids: set = set()
    for p in products.values():
        item_ids |= set(p.get("variants", {}).keys())
    for o in orders.values():
        for it in o.get("items", []):
            if "item_id" in it:
                item_ids.add(it["item_id"])
    payment_ids: set = set()
    emails: set = set()
    for u in users.values():
        payment_ids |= set(u.get("payment_methods", {}).keys())
        if u.get("email"):
            emails.add(u["email"])
    tracking: set = set()
    for o in orders.values():
        for f in o.get("fulfillments", []):
            for t in f.get("tracking_id", []):
                tracking.add(t)
    return {
        "user_id": set(users.keys()),
        "order_id": set(orders.keys()),
        "product_id": set(products.keys()),
        "item_id": item_ids,
        "payment_id": payment_ids,
        "email": emails,
        "tracking_id": tracking,
    }


def _mint(rng: random.Random, ns: str, old: str) -> str:
    if ns == "order_id":
        return "#W" + _digits(rng, 7)
    if ns in ("product_id", "item_id", "tracking_id"):
        # preserve original length so downstream formats stay plausible
        return _digits(rng, max(6, len(old)))
    if ns == "payment_id":
        prefix = old.rsplit("_", 1)[0] if "_" in old else "credit_card"
        return f"{prefix}_{_digits(rng, 7)}"
    if ns == "email":
        return f"user{_digits(rng, 6)}@example.com"
    if ns == "user_id":
        return f"user_{_digits(rng, 8)}"
    return old


def _all_strings(obj: Any, out: set) -> set:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                out.add(k)
            _all_strings(v, out)
    elif isinstance(obj, list):
        for e in obj:
            _all_strings(e, out)
    elif isinstance(obj, str):
        out.add(obj)
    return out


def build_mapping(data: Dict[str, Any], seed: int) -> Dict[str, str]:
    """One combined old->new dict across all namespaces. Id formats are disjoint,
    so exact-string replacement with a single dict is unambiguous. Minted ids avoid
    both prior mints (injectivity) and every string already in the DB (so a fresh id
    can never alias an existing value)."""
    rng = random.Random(seed)
    spaces = _collect(data)
    existing = _all_strings(data, set())
    mapping: Dict[str, str] = {}
    used: set = set()
    for ns in sorted(spaces):  # sorted for determinism
        for old in sorted(spaces[ns]):
            new = _mint(rng, ns, old)
            while new in used or new in existing:  # injective + no aliasing
                new = _mint(rng, ns, old)
            used.add(new)
            mapping[old] = new
    return mapping


# ---- appliers ----------------------------------------------------------------


def deep_remap(obj: Any, mapping: Dict[str, str]) -> Any:
    """Remap dict keys and string values (any string equal to a known id)."""
    if isinstance(obj, dict):
        return {mapping.get(k, k): deep_remap(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_remap(e, mapping) for e in obj]
    if isinstance(obj, str):
        return mapping.get(obj, obj)
    return obj


def rekey_data(data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
    return deep_remap(data, mapping)


def rekey_actions(actions: List[Action], mapping: Dict[str, str]) -> List[Action]:
    return [Action(name=a.name, kwargs=deep_remap(a.kwargs, mapping)) for a in actions]


def rekey_text(text: str, mapping: Dict[str, str]) -> str:
    """Substitute any id token appearing verbatim in free text (e.g. an order id in
    the instruction). Longer keys first to avoid partial-overlap clobbering."""
    if not text:
        return text
    for old in sorted(mapping, key=len, reverse=True):
        if old in text:
            text = text.replace(old, mapping[old])
    return text


def rekey_instance(
    data: Dict[str, Any],
    actions: List[Action],
    instruction: str,
    outputs: List[str],
    seed: int,
) -> Tuple[Dict[str, Any], List[Action], str, List[str], Dict[str, str]]:
    m = build_mapping(data, seed)
    return (
        rekey_data(data, m),
        rekey_actions(actions, m),
        rekey_text(instruction, m),
        [rekey_text(o, m) for o in outputs],
        m,
    )
