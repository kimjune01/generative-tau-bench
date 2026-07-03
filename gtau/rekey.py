"""Seeded, descriptor-driven re-keying of a database-shaped instance.

The load-bearing move of generative tau-bench: because the oracle is computed by
*replaying* a golden action program (not by reading a stored answer), we can alpha-
rename an instance and the oracle re-derives for free. This module builds a seeded
bijection over the id namespaces of a tool-world DB and applies it consistently to
the database, the golden action program, and any text (instruction, outputs). It
names no benchmark: the id namespaces come from a per-domain `id_collections`
descriptor (see gtau/domains.py).

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
import re
import string
from typing import Any, Dict, List, Set, Tuple

from .action import Action

# ---- id space collectors -----------------------------------------------------
# Each namespace: how to find every existing id in the DB, and how to mint a fresh
# one deterministically from the RNG. Fresh ids are drawn without replacement so
# the map is injective within a namespace.


def _digits(rng: random.Random, n: int) -> str:
    return "".join(rng.choice(string.digits) for _ in range(n))


def _letters(rng: random.Random, run: str) -> str:
    """Same-length, case-matching random letters (for digit-less ids like airline's
    six-uppercase reservation codes)."""
    return "".join(
        rng.choice(string.ascii_uppercase if c.isupper() else string.ascii_lowercase)
        for c in run
    )


def _collect(data: Any, id_collections: Set[str]) -> set:
    """All id strings in the instance: the keys of every dict that sits under a field
    named in `id_collections`. Schema-agnostic given that small descriptor, so
    `flights[*].dates` (a date-keyed dict) is left untouched while `users`,
    `reservations`, `payment_methods`, `variants`, etc. are collected. Values that
    reference these ids elsewhere (e.g. `user_id`, `flight_number`, `payment_id`) are
    remapped by exact-string match in deep_remap; they need not be listed."""
    ids: set = set()

    def walk(obj: Any, field) -> None:
        if isinstance(obj, dict):
            if field in id_collections:
                ids.update(k for k in obj if isinstance(k, str))
            for k, v in obj.items():
                walk(v, k)
        elif isinstance(obj, list):
            # list elements are positional, not id-keyed, so they must NOT inherit the
            # collection field. (Guards the 'flights' overload: a top-level flights
            # table vs a reservation's flights list of leg objects.)
            for e in obj:
                walk(e, None)

    walk(data, None)
    return ids


def _mint(rng: random.Random, old: str) -> str:
    """Format-preserving fresh id: regenerate every maximal digit run and leave the
    non-digit structure intact ('#W', 'credit_card_', 'HAT', 'yusuf_rossi_'); for
    digit-less ids (airline's 'HXDUBJ'), regenerate letter runs case-preservingly
    instead. Same-length output, so the original can never survive as a substring —
    the old suffix fallback embedded it ('XEWRD9' -> 'XEWRD9_3602'), a leak the
    soundness audit caught on every digit-less airline reservation id. Collisions
    (new == old) are re-rolled by the caller."""
    if re.search(r"\d", old):
        return re.sub(r"\d+", lambda m: _digits(rng, len(m.group())), old)
    return re.sub(r"[A-Za-z]+", lambda m: _letters(rng, m.group()), old)


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


def build_mapping(data: Any, seed: int, id_collections: Set[str]) -> Dict[str, str]:
    """One combined old->new id dict, format-preserving. Minted ids avoid both prior
    mints (injectivity) and every string already in the DB (so a fresh id can never
    alias an existing value)."""
    rng = random.Random(seed)
    existing = _all_strings(data, set())
    mapping: Dict[str, str] = {}
    used: set = set()
    for old in sorted(_collect(data, id_collections)):  # sorted for determinism
        new = _mint(rng, old)
        while new == old or new in used or new in existing:  # fresh + injective + no aliasing
            new = _mint(rng, old)
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
    id_collections: Set[str],
) -> Tuple[Dict[str, Any], List[Action], str, List[str], Dict[str, str]]:
    m = build_mapping(data, seed, id_collections)
    return (
        rekey_data(data, m),
        rekey_actions(actions, m),
        rekey_text(instruction, m),
        [rekey_text(o, m) for o in outputs],
        m,
    )
