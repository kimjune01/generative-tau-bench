"""Parametric branch-selection: the reachable rung above cosmetic re-keying.

Cosmetic re-keying (`rekey.py`) renames ids and preserves the resolution path
byte-for-byte, so a model that memorized the path still wins. Branch-selection
resamples the DB *content that decides which branch of an authored conditional task
fires*, and derives the golden by evaluating the task's own stated predicate over the
resampled content. Memorizing one resolution path stops transferring, because the
correct branch now varies with the seed.

The oracle stays construction-derived (precondition 3 intact): we never synthesize a
new action shape. The golden's branch targets are variants that already exist in the
catalog, and the selection rule is a boolean predicate read straight off the task
instruction, auditable by a human in finite time. This is exactly the line the
regeneration ladder in DESIGN.md draws between rung 2 (trustworthy) and rung 3
(LLM-as-golden, disqualified).

Currently one spec ships: retail base task 0 (Yusuf Rossi's keyboard/thermostat
exchange), whose instruction states the conditional explicitly:

    "...exchange the mechanical keyboard for a similar one but with clicky switches
     ... If there is no keyboard that is clicky, RGB backlight, full size, you'd go
     for no backlight."

The predicate is "an available (clicky, RGB, full size) keyboard variant exists."
In shipped tau-bench it is False (variant 9025753381 is unavailable), so the golden
takes the no-backlight fallback (7706410293). Toggling that one availability flag by
seed flips the branch, and the correct exchange target moves with it.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import copy
import hashlib

from .action import Action
from .replay import oracle_hash
from .domains import Domain, DOMAINS


def _seed_bool(seed: int, salt: str) -> bool:
    """Deterministic, well-mixed branch bit from a seed (avoids raw parity so that
    consecutive seeds don't lock-step the branch)."""
    h = hashlib.sha256(f"{salt}:{seed}".encode()).digest()
    return bool(h[0] & 1)


@dataclass
class VariantPredicate:
    """A branch condition: 'an available variant of `product_id` with these options
    exists.' The target when true is that variant; the pivot is the variant whose
    availability we toggle to realize the branch."""
    product_id: str
    options: Dict[str, str]        # e.g. {"switch type": "clicky", "backlight": "RGB", "size": "full size"}

    def matching_variant(self, products: Dict[str, Any]) -> Optional[str]:
        """The id of the variant whose options == self.options (available or not)."""
        for vid, v in products[self.product_id]["variants"].items():
            if v.get("options") == self.options:
                return vid
        return None

    def available_match(self, products: Dict[str, Any]) -> Optional[str]:
        """The id of an *available* variant matching self.options, else None."""
        vid = self.matching_variant(products)
        if vid is not None and products[self.product_id]["variants"][vid]["available"]:
            return vid
        return None


@dataclass
class ExchangeBranchSpec:
    """Branch-selection over one exchange-delivered-order task.

    The golden is: read user + order + products, then one exchange action whose
    keyboard target is chosen by `primary` (if its variant is available) else
    `fallback`. The thermostat leg is invariant to the branch.
    """
    domain: str
    base_task_index: int
    # user / order identity (read legs + exchange target order)
    find_user_kwargs: Dict[str, str]
    order_id: str
    payment_method_id: str
    read_product_ids: List[str]          # get_product_details legs (faithful to base task)
    # the item the user owns and swaps out (keyboard) + its branch targets
    owned_keyboard_item: str
    primary: VariantPredicate            # clicky + RGB + full size
    fallback: VariantPredicate           # clicky + no backlight + full size
    # invariant thermostat leg
    thermostat_old_item: str
    thermostat_new_item: str

    def resample(self, base_data: Dict[str, Any], seed: int) -> Tuple[Dict[str, Any], bool]:
        """Fresh DB for `seed`: toggle availability of the primary variant so the
        branch predicate is True on ~half of seeds. Returns (data, primary_fires)."""
        data = copy.deepcopy(base_data)
        products = data["products"]
        pivot = self.primary.matching_variant(products)
        if pivot is None:
            raise ValueError("primary variant not found in catalog; spec is stale")
        primary_fires = _seed_bool(seed, salt=f"{self.domain}:{self.base_task_index}")
        products[self.primary.product_id]["variants"][pivot]["available"] = primary_fires
        return data, primary_fires

    def derive_golden(self, data: Dict[str, Any]) -> Tuple[List[Action], str]:
        """Evaluate the instruction's stated predicate over `data` and build the
        golden. Returns (actions, branch_label). Construction guarantees solvability:
        the chosen keyboard target is always an available variant."""
        products = data["products"]
        target = self.primary.available_match(products)
        branch = "primary"
        if target is None:
            target = self.fallback.available_match(products)
            branch = "fallback"
        if target is None:
            raise ValueError("neither primary nor fallback keyboard variant is available")

        actions = [
            Action("find_user_id_by_name_zip", dict(self.find_user_kwargs)),
            Action("get_order_details", {"order_id": self.order_id}),
        ]
        actions += [Action("get_product_details", {"product_id": pid}) for pid in self.read_product_ids]
        actions.append(Action("exchange_delivered_order_items", {
            "order_id": self.order_id,
            "item_ids": [self.owned_keyboard_item, self.thermostat_old_item],
            "new_item_ids": [target, self.thermostat_new_item],
            "payment_method_id": self.payment_method_id,
        }))
        return actions, branch


# --- shipped spec: retail base task 0 -------------------------------------------------

RETAIL_KEYBOARD_EXCHANGE = ExchangeBranchSpec(
    domain="retail",
    base_task_index=0,
    find_user_kwargs={"first_name": "Yusuf", "last_name": "Rossi", "zip": "19122"},
    order_id="#W2378156",
    payment_method_id="credit_card_9513926",
    read_product_ids=["1656367028", "4896585277"],
    owned_keyboard_item="1151293680",
    primary=VariantPredicate("1656367028", {"switch type": "clicky", "backlight": "RGB", "size": "full size"}),
    fallback=VariantPredicate("1656367028", {"switch type": "clicky", "backlight": "none", "size": "full size"}),
    thermostat_old_item="4983901480",
    thermostat_new_item="7747408585",
)

BRANCH_SPECS: Dict[str, ExchangeBranchSpec] = {"retail:0": RETAIL_KEYBOARD_EXCHANGE}


@dataclass
class BranchInstance:
    seed: int
    data: Dict[str, Any]
    golden: List[Action]
    instruction: str
    oracle: str
    branch: str                          # "primary" | "fallback"
    domain: str = "retail"
    outputs: List[str] = field(default_factory=list)   # required strings, from the base task
    mapping: Dict[str, str] = field(default_factory=dict, repr=False)


def _resolve(domain) -> Domain:
    return DOMAINS[domain] if isinstance(domain, str) else domain


def generate_branch_instance(spec: ExchangeBranchSpec, seed: int) -> BranchInstance:
    """Resample the branch-deciding content by seed, derive the golden by predicate,
    and re-derive the oracle by replay. Solvable and trustworthy by construction."""
    dom = _resolve(spec.domain)
    base_data = dom.load_data()
    data, _ = spec.resample(base_data, seed)
    golden, branch = spec.derive_golden(data)
    base_task = dom.tasks()[spec.base_task_index]
    return BranchInstance(
        seed=seed,
        data=data,
        golden=golden,
        instruction=base_task.instruction,
        oracle=oracle_hash(golden, data, dom.tools()),
        branch=branch,
        domain=dom.name,
        outputs=list(getattr(base_task, "outputs", []) or []),
    )
