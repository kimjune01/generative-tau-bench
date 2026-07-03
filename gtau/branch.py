"""Parametric branch-selection: the reachable rung above cosmetic re-keying.

Cosmetic re-keying (`rekey.py`) renames ids and preserves the resolution path
byte-for-byte, so a model that memorized the path still wins. Branch-selection
resamples the DB *content that decides which branch of an authored conditional task
fires*, and derives the golden by evaluating the task's own stated predicate over the
resampled content. Memorizing one resolution path stops transferring, because the
correct branch now varies with the seed.

The oracle stays construction-derived (precondition 3 intact): we never synthesize a
new action shape and never consult an LLM. The golden's branch targets are variants
that already exist in the catalog, and the selection rule is a predicate read straight
off the task instruction, auditable by a human in finite time. This is exactly the
line the regeneration ladder in DESIGN.md draws between rung 2 (trustworthy) and
rung 3 (LLM-as-golden, disqualified).

The engine is a three-part algebra (see docs/BRANCHABLE_TASKS.md for the inventory):

  (a) a seeded resampler: each spec declares its realizable `World`s — canonical
      availability patterns over the pivot variants — and the seed picks one
      (uniformly, so every realizable branch fires with substantial probability);
  (b) a selector — the instruction's stated predicate, either `FirstAvailable`
      (a preference cascade) or `BestAvailable` (argmin/argmax over available
      variants) — evaluated over the resampled catalog to pick the target;
  (c) a golden builder: the shipped task's action list with the branch-decided
      slot(s) substituted (identity substitution on the shipped branch, so the
      shipped world reproduces the shipped golden byte-for-byte).

Shipped specs (all retail; "retail:<base task index>"):

  0   keyboard exchange, RGB else no backlight (the original ExchangeBranchSpec)
  1   same predicate; on False the keyboard drops out of the exchange entirely
  6-9 desk-lamp preference cascades (battery/USB/AC permutations, low/high brightness)
  41  jigsaw argmin (easiest difficulty, fewest pieces); 42 same predicate re-stated
  44  cheapest desk lamp (argmin price) — task.outputs co-derived (refund = owned
      price minus chosen price; shipped '17.99' only holds on the shipped branch)
  79  exact 1000ml bottle else relax material — ships on its PRIMARY branch
      (inventory surprise #3: shipped != fallback)
  97/98 cheapest green speaker (argmin price over green variants)
  107 XL cotton t-shirt, black if multiple colors (a 2-rung cascade: black, else
      the lone remaining color)

Excluded from the EASY set (honest denominator):

  83  deferred, not failed: the pivot is `orders[...].payment_history[0]
      .payment_method_id`, an order field, not catalog availability — a different
      resampler shape (and it must stay consistent with the user's payment_methods).
      Nothing here blocks it; it just isn't this algebra.

Spec-local pins (documented so the audit trail stays honest):

  - tasks 8/9: the catalog holds a second high-brightness AC lamp (4385534692,
    white, shipped-unavailable). The instruction ranks power sources, not colors,
    so a world where both AC variants are available leaves the golden
    underdetermined. Worlds keep 4385534692 at its shipped value (unavailable);
    the cascade ranges over {1270145486, 9083642334, 7624783998} only.
  - task 42: the "if not shipped yet" guard stays satisfied (the order ships
    pending and worlds never touch order status); using status as a second pivot
    would create a no-op branch and is out of scope for the EASY set.
  - task 79: the fallback ("allow the material to be different") is anchored to
    1434748144 {1000ml, glass, red} — same capacity and color as the exact item,
    material relaxed; it exists shipped-unavailable, so the fallback world forces
    it available (the same solvability-by-construction move as task 0).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
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


def _seed_choice(seed: int, salt: str, k: int) -> int:
    """Deterministic, well-mixed choice of one of k realizable worlds."""
    h = hashlib.sha256(f"{salt}:{seed}".encode()).digest()
    return int.from_bytes(h[:4], "big") % k


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

    # branch bookkeeping (shared interface with CatalogBranchSpec)
    @property
    def expected_branches(self) -> Tuple[str, ...]:
        return ("primary", "fallback")

    @property
    def shipped_branch(self) -> str:
        return "fallback"                # 9025753381 ships unavailable

    def resample(self, base_data: Dict[str, Any], seed: int) -> Tuple[Dict[str, Any], str]:
        """Fresh DB for `seed`: toggle availability of the primary variant so the
        branch predicate is True on ~half of seeds. Returns (data, world_label)."""
        data = copy.deepcopy(base_data)
        products = data["products"]
        pivot = self.primary.matching_variant(products)
        if pivot is None:
            raise ValueError("primary variant not found in catalog; spec is stale")
        primary_fires = _seed_bool(seed, salt=f"{self.domain}:{self.base_task_index}")
        products[self.primary.product_id]["variants"][pivot]["available"] = primary_fires
        return data, ("primary" if primary_fires else "fallback")

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


# --- the generic algebra: worlds x selector x template patch -------------------------

Pivot = Tuple[str, str]  # (product_id, variant_id)


@dataclass
class World:
    """One realizable branch's canonical catalog pattern: availability flags forced
    on the pivot variants; every unmentioned variant keeps its shipped value. The
    world whose pattern equals the shipped flags reproduces the shipped DB exactly,
    which is what makes the byte-for-byte faithfulness anchor possible."""
    label: str
    avail: Dict[Pivot, bool]


@dataclass
class FirstAvailable:
    """The instruction's stated preference cascade: the first available variant in
    `preference` order. `none_ok=True` models tasks whose last rung is 'then do
    less' (task 1: drop the keyboard leg) rather than another catalog target."""
    product_id: str
    preference: List[str]          # variant ids, in the instruction's stated order
    none_ok: bool = False

    def select(self, products: Dict[str, Any]) -> Optional[str]:
        variants = products[self.product_id]["variants"]
        for vid in self.preference:
            if variants[vid]["available"]:
                return vid
        if self.none_ok:
            return None
        raise ValueError(f"no cascade candidate of {self.product_id} is available; "
                         "resampler and selector disagree — spec is stale")


@dataclass
class BestAvailable:
    """argmin (argmax with reverse=True) of `key` over the available variants of
    `product_id` whose options match `where`. Raises on a tie: a tied extremum means
    the instruction underdetermines the golden, and we refuse to guess."""
    product_id: str
    key: Callable[[Dict[str, Any]], Any]
    where: Dict[str, str] = field(default_factory=dict)
    reverse: bool = False

    def select(self, products: Dict[str, Any]) -> str:
        variants = products[self.product_id]["variants"]
        ranked = sorted(
            ((self.key(v), vid) for vid, v in variants.items()
             if v["available"] and all(v["options"].get(k) == want for k, want in self.where.items())),
            reverse=self.reverse,
        )
        if not ranked:
            raise ValueError(f"no available variant of {self.product_id} matches {self.where}")
        if len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
            raise ValueError(f"tie on {self.product_id} at {ranked[0][0]}: golden underdetermined")
        return ranked[0][1]


def _substitute(obj: Any, mapping: Dict[str, str]) -> Any:
    """Apply string substitutions through kwargs values (strings, lists, dicts)."""
    if isinstance(obj, str):
        for old, new in mapping.items():
            obj = obj.replace(old, new)
        return obj
    if isinstance(obj, list):
        return [_substitute(x, mapping) for x in obj]
    if isinstance(obj, dict):
        return {k: _substitute(v, mapping) for k, v in obj.items()}
    return obj


@dataclass
class CatalogBranchSpec:
    """Branch-selection over one task whose conditional is a predicate on catalog
    availability. Composition: seed -> World (canonical availability pattern) ->
    selector (the instruction's predicate) -> golden (shipped action template with
    the branch-decided slot substituted).

    derive_golden never looks at which world the resampler chose — it re-evaluates
    the instruction's predicate on the data, so a stale spec (worlds and selector
    disagreeing) shows up as a test failure, not a silently wrong oracle.
    """
    domain: str
    base_task_index: int
    worlds: List[World]
    selector: Union[FirstAvailable, BestAvailable]
    shipped_branch: str
    # default golden builder: substitute the shipped target id with the selected one
    shipped_target: Optional[str] = None
    # branch label per selected target (default: the target variant id itself)
    labels: Dict[Optional[str], str] = field(default_factory=dict)
    # overrides for tasks whose golden changes shape (task 1) or quotes derived
    # values (task 44's calculate expression / outputs)
    patch: Optional[Callable[[List[Action], Optional[str], Dict[str, Any]], List[Action]]] = None
    substitutions: Optional[Callable[[Dict[str, Any], str], Dict[str, str]]] = None
    derive_outputs_fn: Optional[Callable[[Dict[str, Any], Optional[str]], List[str]]] = None
    notes: str = ""

    @property
    def expected_branches(self) -> Tuple[str, ...]:
        return tuple(w.label for w in self.worlds)

    def _label(self, target: Optional[str]) -> str:
        if target in self.labels:
            return self.labels[target]
        return target if target is not None else "none"

    def _base_actions(self) -> List[Action]:
        dom = _resolve(self.domain)
        return [Action.from_tau(a) for a in dom.tasks()[self.base_task_index].actions]

    def resample(self, base_data: Dict[str, Any], seed: int) -> Tuple[Dict[str, Any], str]:
        """Fresh DB for `seed`: pick one realizable world uniformly and force its
        canonical availability pattern. Uniform choice makes every realizable branch
        fire with probability 1/k across seeds. Returns (data, world_label)."""
        data = copy.deepcopy(base_data)
        world = self.worlds[_seed_choice(seed, f"{self.domain}:{self.base_task_index}", len(self.worlds))]
        for (pid, vid), flag in world.avail.items():
            data["products"][pid]["variants"][vid]["available"] = flag
        return data, world.label

    def derive_golden(self, data: Dict[str, Any]) -> Tuple[List[Action], str]:
        """Evaluate the instruction's predicate over `data`, then emit the shipped
        action template with the branch-decided slots substituted. On the shipped
        branch the substitution is the identity, so the golden reproduces the
        shipped task byte-for-byte."""
        target = self.selector.select(data["products"])
        actions = self._base_actions()
        if self.patch is not None:
            actions = self.patch(actions, target, data)
        if target is not None and self.shipped_target is not None:
            mapping = (self.substitutions(data, target) if self.substitutions is not None
                       else {self.shipped_target: target})
            actions = [Action(a.name, _substitute(a.kwargs, mapping)) for a in actions]
        return actions, self._label(target)

    def derive_outputs(self, data: Dict[str, Any]) -> Optional[List[str]]:
        """Co-derive task.outputs from the resampled catalog where the shipped
        outputs quote pivoted content (inventory surprise #5). None = keep the base
        task's outputs (they are branch-invariant)."""
        if self.derive_outputs_fn is None:
            return None
        return self.derive_outputs_fn(data, self.selector.select(data["products"]))


def _cascade_worlds(product_id: str, rungs: List[str],
                    labels: Optional[Dict[str, str]] = None) -> List[World]:
    """Canonical worlds for a k-rung preference cascade: world i turns rung i on and
    every earlier rung off; later rungs keep their shipped flags. The world matching
    the shipped first-available rung therefore equals the shipped DB exactly."""
    labels = labels or {}
    return [
        World(label=labels.get(vid, vid),
              avail={**{(product_id, r): False for r in rungs[:i]}, (product_id, vid): True})
        for i, vid in enumerate(rungs)
    ]


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


# --- retail task 1: same predicate as 0; on False the keyboard leg drops out ---------

_KEYBOARD = "1656367028"
_KB_PRIMARY = "9025753381"           # clicky + RGB + full size (ships unavailable)


def _task1_patch(actions: List[Action], target: Optional[str], data: Dict[str, Any]) -> List[Action]:
    """Shipped golden IS the fallback (thermostat-only exchange). On the primary
    branch the keyboard joins the exchange, mirroring task 0's primary golden."""
    if target is None:
        return actions
    exchange = actions[-1]
    exchange.kwargs["item_ids"] = ["1151293680", "4983901480"]
    exchange.kwargs["new_item_ids"] = [target, "7747408585"]
    return actions


RETAIL_1 = CatalogBranchSpec(
    domain="retail",
    base_task_index=1,
    worlds=[
        World("primary", {(_KEYBOARD, _KB_PRIMARY): True}),
        World("fallback", {(_KEYBOARD, _KB_PRIMARY): False}),   # == shipped DB
    ],
    selector=FirstAvailable(_KEYBOARD, [_KB_PRIMARY], none_ok=True),
    shipped_branch="fallback",
    labels={_KB_PRIMARY: "primary", None: "fallback"},
    patch=_task1_patch,
    notes="branch decides list membership, not one list element",
)


# --- retail tasks 6-9: desk-lamp preference cascades ----------------------------------

_LAMP = "6817146515"
_LAMP_LOW = {"battery": "7453605304", "USB": "9190635437", "AC": "1569765161"}
_LAMP_HIGH = {"battery": "1270145486", "USB": "9083642334", "AC": "7624783998"}
# NOTE: high-brightness AC also exists as 4385534692 (white, ships unavailable);
# it stays pinned at its shipped value in every world — see the module docstring.


def _lamp_cascade_spec(index: int, pool: Dict[str, str], order: List[str],
                       shipped_branch: str, shipped_target: str) -> CatalogBranchSpec:
    rungs = [pool[p] for p in order]
    return CatalogBranchSpec(
        domain="retail",
        base_task_index=index,
        worlds=_cascade_worlds(_LAMP, rungs),
        selector=FirstAvailable(_LAMP, rungs),
        shipped_branch=shipped_branch,
        shipped_target=shipped_target,
        notes=f"preference {' > '.join(order)} over the "
              f"{'low' if pool is _LAMP_LOW else 'high'}-brightness pool",
    )


RETAIL_6 = _lamp_cascade_spec(6, _LAMP_LOW, ["battery", "USB", "AC"],
                              shipped_branch=_LAMP_LOW["battery"], shipped_target="7453605304")
RETAIL_7 = _lamp_cascade_spec(7, _LAMP_LOW, ["AC", "battery", "USB"],
                              shipped_branch=_LAMP_LOW["AC"], shipped_target="1569765161")
RETAIL_8 = _lamp_cascade_spec(8, _LAMP_HIGH, ["battery", "USB", "AC"],
                              shipped_branch=_LAMP_HIGH["USB"], shipped_target="9083642334")
RETAIL_9 = _lamp_cascade_spec(9, _LAMP_HIGH, ["AC", "battery", "USB"],
                              shipped_branch=_LAMP_HIGH["AC"], shipped_target="7624783998")


# --- retail tasks 41/42: easiest jigsaw, fewest pieces (lexicographic argmin) ---------

_JIGSAW = "1808611083"
_JIGSAW_DIFFICULTY = {"beginner": 0, "intermediate": 1, "expert": 2}


def _jigsaw_easiness(v: Dict[str, Any]) -> Tuple[int, int]:
    o = v["options"]
    return (_JIGSAW_DIFFICULTY[o["difficulty level"]], int(o["pieces"]))


def _jigsaw_spec(index: int) -> CatalogBranchSpec:
    # pivot beginners, cheapest-to-flip first; all other beginner variants ship
    # unavailable, so the all-off world's argmin falls to intermediate/500.
    b500, b1000, b1500 = "1096508426", "4772738468", "9665100170"
    worlds = _cascade_worlds(_JIGSAW, [b500, b1000, b1500])
    worlds.append(World("4068787148", {(_JIGSAW, v): False for v in (b500, b1000, b1500)}))
    return CatalogBranchSpec(
        domain="retail",
        base_task_index=index,
        worlds=worlds,
        selector=BestAvailable(_JIGSAW, key=_jigsaw_easiness),
        shipped_branch=b500,
        shipped_target=b500,
        notes="task 42 restates the same predicate behind an 'if not shipped yet' "
              "guard; the order ships pending and worlds never touch status",
    )


RETAIL_41 = _jigsaw_spec(41)
RETAIL_42 = _jigsaw_spec(42)


# --- retail task 44: cheapest desk lamp (argmin price), outputs co-derived -----------

_TASK44_ORDER = "#W9300146"
_TASK44_OWNED = "9190635437"         # the lamp in the order ($153.23)


def _price(v: Dict[str, Any]) -> float:
    return v["price"]


def _task44_owned_price(data: Dict[str, Any]) -> float:
    return next(i["price"] for i in data["orders"][_TASK44_ORDER]["items"]
                if i["item_id"] == _TASK44_OWNED)


def _task44_substitutions(data: Dict[str, Any], target: str) -> Dict[str, str]:
    """The golden quotes the chosen price inside a `calculate` expression
    ('135.24 - 153.23'); rewrite it alongside the target id."""
    price = data["products"][_LAMP]["variants"][target]["price"]
    return {"5320792178": target, "135.24": f"{price}"}


def _task44_outputs(data: Dict[str, Any], target: Optional[str]) -> List[str]:
    """task.outputs quotes the refund (owned price - chosen price): '17.99' shipped,
    '10.21' and '3.22' on the other realizable branches."""
    price = data["products"][_LAMP]["variants"][target]["price"]
    return [f"{_task44_owned_price(data) - price:.2f}"]


RETAIL_44 = CatalogBranchSpec(
    domain="retail",
    base_task_index=44,
    worlds=[
        World("5320792178", {(_LAMP, "5320792178"): True}),                              # == shipped
        World("1569765161", {(_LAMP, "5320792178"): False, (_LAMP, "1569765161"): True}),
        World("7453605304", {(_LAMP, "5320792178"): False, (_LAMP, "1569765161"): False}),
    ],
    selector=BestAvailable(_LAMP, key=_price),
    shipped_branch="5320792178",
    shipped_target="5320792178",
    substitutions=_task44_substitutions,
    derive_outputs_fn=_task44_outputs,
    notes="every realizable argmin ($135.24/$143.02/$150.01) is cheaper than the "
          "owned lamp ($153.23), so the refund stays positive on all branches",
)


# --- retail task 79: exact 1000ml bottle, else relax material -------------------------

_BOTTLE = "8310926033"

RETAIL_79 = CatalogBranchSpec(
    domain="retail",
    base_task_index=79,
    worlds=[
        World("primary", {(_BOTTLE, "2439754078"): True}),                               # == shipped
        World("fallback", {(_BOTTLE, "2439754078"): False, (_BOTTLE, "1434748144"): True}),
    ],
    selector=FirstAvailable(_BOTTLE, ["2439754078", "1434748144"]),
    shipped_branch="primary",
    shipped_target="2439754078",
    labels={"2439754078": "primary", "1434748144": "fallback"},
    notes="ships on the PRIMARY branch (surprise #3); the fallback world forces the "
          "glass twin available, the solvability-by-construction move",
)


# --- retail tasks 97/98: cheapest green bluetooth speaker -----------------------------

_SPEAKER = "4768869376"


def _green_speaker_spec(index: int) -> CatalogBranchSpec:
    g292, g295, g298 = "5967152432", "2652637226", "9440686670"
    return CatalogBranchSpec(
        domain="retail",
        base_task_index=index,
        worlds=[
            World(g292, {(_SPEAKER, g292): True}),
            World(g295, {(_SPEAKER, g292): False, (_SPEAKER, g295): True}),
            World(g298, {(_SPEAKER, g292): False, (_SPEAKER, g295): False}),             # == shipped
        ],
        selector=BestAvailable(_SPEAKER, key=_price, where={"color": "green"}),
        shipped_branch=g298,
        shipped_target=g298,
        notes="shipped DB has only one green available, making the argmin trivial; "
              "the cheaper greens ship unavailable and flip it when forced on",
    )


RETAIL_97 = _green_speaker_spec(97)
RETAIL_98 = _green_speaker_spec(98)


# --- retail task 107: XL cotton t-shirt, black if multiple colors ---------------------

_TSHIRT = "9523456873"

RETAIL_107 = CatalogBranchSpec(
    domain="retail",
    base_task_index=107,
    worlds=[
        World("2060066974", {(_TSHIRT, "2060066974"): True}),                            # == shipped
        World("8124970213", {(_TSHIRT, "2060066974"): False, (_TSHIRT, "8124970213"): True}),
    ],
    selector=FirstAvailable(_TSHIRT, ["2060066974", "8124970213"]),
    shipped_branch="2060066974",
    shipped_target="2060066974",
    notes="the XL-cotton pool is exactly {black, purple}, so 'black if multiple "
          "colors, else the available one' reduces to the cascade [black, purple]",
)


# --- retail task 29: shorter (28-inch) bamboo skateboard, most expensive if several -----

_SKATEBOARD = "1968349452"

RETAIL_29 = CatalogBranchSpec(
    domain="retail",
    base_task_index=29,
    worlds=[
        World("8176740019", {}),                                                         # == shipped (argmax)
        World("6673921677", {(_SKATEBOARD, "8176740019"): False}),
        World("6843647669", {(_SKATEBOARD, "8176740019"): False, (_SKATEBOARD, "6673921677"): False}),
    ],
    selector=BestAvailable(_SKATEBOARD, key=_price,
                           where={"deck material": "bamboo", "length": "28 inch"}, reverse=True),
    shipped_branch="8176740019",
    shipped_target="8176740019",
    notes="argmax price over available 28-inch bamboo skateboards ($208.60/$189.57/$180.10); "
          "second exchange leg invariant; shipped outputs quote the option prices (co-vary, "
          "not re-derived here — soundness is on end-state)",
)


# --- retail task 74: i9 laptop, prefer 256GB SSD then silver (cascade) ------------------

_LAPTOP = "4760268021"

RETAIL_74 = CatalogBranchSpec(
    domain="retail",
    base_task_index=74,
    worlds=[
        World("3265035808", {}),                                                         # == shipped (256GB silver i9)
        World("2913673670", {(_LAPTOP, "3265035808"): False}),
    ],
    selector=FirstAvailable(_LAPTOP, ["3265035808", "2913673670"]),
    shipped_branch="3265035808",
    shipped_target="3265035808",
    notes="i9 laptop, prefer 256GB then silver; the two available i9 variants are "
          "3265035808 (256GB silver) and 2913673670 (512GB black); cancel leg invariant",
)


# --- retail tasks 110/111: cheapest tablet (argmin price) -------------------------------

_TABLET = "8024098596"


def _cheapest_tablet_spec(index: int) -> CatalogBranchSpec:
    return CatalogBranchSpec(
        domain="retail",
        base_task_index=index,
        worlds=[
            World("2106335193", {}),                                                     # == shipped (argmin $903.95)
            World("4913411651", {(_TABLET, "2106335193"): False}),                       # -> $941.03
            World("6948061616", {(_TABLET, "2106335193"): False, (_TABLET, "4913411651"): False}),  # -> $950.96
        ],
        selector=BestAvailable(_TABLET, key=_price),
        shipped_branch="2106335193",
        shipped_target="2106335193",
        notes="cheapest available tablet (argmin price); every realizable argmin stays below "
              "the owned tablet ($1018.68) so the modify is never a no-op; address legs invariant",
    )


RETAIL_110 = _cheapest_tablet_spec(110)
RETAIL_111 = _cheapest_tablet_spec(111)


# --- retail task 70: helmet M/high-vent, blue if multiple colors -----------------------

_HELMET = "7765186836"

RETAIL_70 = CatalogBranchSpec(
    domain="retail",
    base_task_index=70,
    worlds=[
        World("9013366374", {}),                                                         # == shipped (blue present)
        World("8573379326", {(_HELMET, "9013366374"): False}),                           # blue gone -> red
    ],
    selector=FirstAvailable(_HELMET, ["9013366374", "8573379326"]),
    shipped_branch="9013366374",
    shipped_target="9013366374",
    notes="M/high-vent helmet pool is {blue 9013366374, red 8573379326}; 'blue if multiple "
          "colors else the available one' reduces to the cascade [blue, red] (cf. task 107)",
)


# --- retail tasks 102/103: metal watch, white if multiple colors -----------------------

_WATCH = "6066914160"


def _metal_watch_spec(index: int) -> CatalogBranchSpec:
    return CatalogBranchSpec(
        domain="retail",
        base_task_index=index,
        worlds=[
            World("2407258246", {}),                                                     # == shipped (white present)
            World("4510078629", {(_WATCH, "2407258246"): False}),                        # white gone -> black
        ],
        selector=FirstAvailable(_WATCH, ["2407258246", "4510078629"]),
        shipped_branch="2407258246",
        shipped_target="2407258246",
        notes="available metal watches are {white 2407258246, black 4510078629} (metal blue "
              "ships unavailable, left off); 'white if multiple' reduces to [white, black]",
    )


RETAIL_102 = _metal_watch_spec(102)
RETAIL_103 = _metal_watch_spec(103)


# --- retail task 45: canister vacuum, bagless if several options -----------------------

_VACUUM = "1762337868"

RETAIL_45 = CatalogBranchSpec(
    domain="retail",
    base_task_index=45,
    worlds=[
        World("7958300294", {}),                                                         # == shipped (several -> bagless)
        World("1345513440", {(_VACUUM, "7958300294"): False, (_VACUUM, "2872451762"): False}),  # single bagged
        World("2872451762", {(_VACUUM, "7958300294"): False, (_VACUUM, "1345513440"): False}),  # single bagged
    ],
    selector=FirstAvailable(_VACUUM, ["7958300294", "1345513440", "2872451762"]),
    shipped_branch="7958300294",
    shipped_target="7958300294",
    notes="'bagless iff several canister options, else the single available one': the shipped "
          "world exposes several (-> bagless 7958300294); the fallback worlds expose exactly "
          "one canister so 'the single available one' is well-posed",
)


# --- retail task 60: blue earbuds <= owned price, no water resistance if several -------

_EARBUDS = "9924732112"

RETAIL_60 = CatalogBranchSpec(
    domain="retail",
    base_task_index=60,
    worlds=[
        World("6077640618", {}),                                                         # == shipped (several -> not-resistant)
        World("8555936349", {(_EARBUDS, "6077640618"): False, (_EARBUDS, "1646531091"): False}),
        World("1646531091", {(_EARBUDS, "6077640618"): False, (_EARBUDS, "8555936349"): False}),
    ],
    selector=FirstAvailable(_EARBUDS, ["6077640618", "8555936349", "1646531091"]),
    shipped_branch="6077640618",
    shipped_target="6077640618",
    notes="qualifying blue earbuds <= owned price are {6077640618 not-resistant, 8555936349, "
          "1646531091} (all IPX4); 'no water resistance if several' -> not-resistant when "
          "several, else the single available one",
)


# --- retail tasks 99/100: +1000-piece same-difficulty jigsaw, animal/art preference ----

_JIGSAW = "1808611083"


def _jigsaw_theme_spec(index: int, preference: List[str], shipped_target: str) -> CatalogBranchSpec:
    return CatalogBranchSpec(
        domain="retail",
        base_task_index=index,
        worlds=[
            World(preference[0], {}),                                                    # == shipped (both present -> preferred)
            World(preference[1], {(_JIGSAW, preference[0]): False}),
        ],
        selector=FirstAvailable(_JIGSAW, preference),
        shipped_branch=preference[0],
        shipped_target=shipped_target,
        notes="1500-piece intermediate jigsaws are {animals 6245746168, art 5546244844}; "
              "task 99 prefers animal, 100 prefers art — the two ship as each other's branches",
    )


RETAIL_99 = _jigsaw_theme_spec(99, ["6245746168", "5546244844"], "6245746168")
RETAIL_100 = _jigsaw_theme_spec(100, ["5546244844", "6245746168"], "5546244844")


# --- retail task 91: e-reader self-exchange if available online, else return -----------

_EREADER = "3801771308"


def _task91_patch(actions: List[Action], target: Optional[str], data: Dict[str, Any]) -> List[Action]:
    """Shipped golden IS the primary (self-exchange of the owned e-reader 9494281769,
    which ships available). When forced unavailable, return it instead. The first leg
    (returning the two skateboards in #W7553978) is invariant."""
    if target is not None:
        return actions
    return actions[:-1] + [Action("return_delivered_order_items", {
        "order_id": "#W3239882",
        "item_ids": ["9494281769"],
        "payment_method_id": "credit_card_5902940",
    })]


RETAIL_91 = CatalogBranchSpec(
    domain="retail",
    base_task_index=91,
    worlds=[
        World("exchange", {}),                                                           # == shipped (9494281769 available)
        World("return", {(_EREADER, "9494281769"): False}),
    ],
    selector=FirstAvailable(_EREADER, ["9494281769"], none_ok=True),
    shipped_branch="exchange",
    labels={"9494281769": "exchange", None: "return"},
    patch=_task91_patch,
    notes="branch flips the action: e-reader available online -> self-exchange (shipped); "
          "else return in #W3239882. Non-shipped (return) branch reconstructed from intent",
)


BranchSpec = Union[ExchangeBranchSpec, CatalogBranchSpec]

BRANCH_SPECS: Dict[str, BranchSpec] = {
    "retail:0": RETAIL_KEYBOARD_EXCHANGE,
    "retail:1": RETAIL_1,
    "retail:6": RETAIL_6,
    "retail:7": RETAIL_7,
    "retail:8": RETAIL_8,
    "retail:9": RETAIL_9,
    "retail:41": RETAIL_41,
    "retail:42": RETAIL_42,
    "retail:44": RETAIL_44,
    "retail:79": RETAIL_79,
    "retail:97": RETAIL_97,
    "retail:98": RETAIL_98,
    "retail:107": RETAIL_107,
    "retail:29": RETAIL_29,
    "retail:74": RETAIL_74,
    "retail:110": RETAIL_110,
    "retail:111": RETAIL_111,
    "retail:70": RETAIL_70,
    "retail:102": RETAIL_102,
    "retail:103": RETAIL_103,
    "retail:45": RETAIL_45,
    "retail:60": RETAIL_60,
    "retail:99": RETAIL_99,
    "retail:100": RETAIL_100,
    "retail:91": RETAIL_91,
}


@dataclass
class BranchInstance:
    seed: int
    data: Dict[str, Any]
    golden: List[Action]
    instruction: str
    oracle: str
    branch: str                          # world label, e.g. "primary" | "fallback" | target variant id
    domain: str = "retail"
    outputs: List[str] = field(default_factory=list)   # required strings, co-derived where pivoted
    mapping: Dict[str, str] = field(default_factory=dict, repr=False)


def _resolve(domain) -> Domain:
    return DOMAINS[domain] if isinstance(domain, str) else domain


_BASE_DATA_CACHE: Dict[str, Dict[str, Any]] = {}


def _base_data(dom: Domain) -> Dict[str, Any]:
    """Domain data is static JSON; load it once. Safe to share: resample deep-copies
    before mutating, and callers never write through this reference."""
    if dom.name not in _BASE_DATA_CACHE:
        _BASE_DATA_CACHE[dom.name] = dom.load_data()
    return _BASE_DATA_CACHE[dom.name]


def generate_branch_instance(spec: BranchSpec, seed: int,
                             base_data: Optional[Dict[str, Any]] = None) -> BranchInstance:
    """Resample the branch-deciding content by seed, derive the golden by predicate,
    and re-derive the oracle by replay. Solvable and trustworthy by construction."""
    dom = _resolve(spec.domain)
    if base_data is None:
        base_data = _base_data(dom)
    data, _ = spec.resample(base_data, seed)
    golden, branch = spec.derive_golden(data)
    base_task = dom.tasks()[spec.base_task_index]
    outputs = spec.derive_outputs(data) if hasattr(spec, "derive_outputs") else None
    if outputs is None:
        outputs = list(getattr(base_task, "outputs", []) or [])
    return BranchInstance(
        seed=seed,
        data=data,
        golden=golden,
        instruction=base_task.instruction,
        oracle=oracle_hash(golden, data, dom.tools()),
        branch=branch,
        domain=dom.name,
        outputs=outputs,
    )
