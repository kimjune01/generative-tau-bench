"""Replay a golden action program against a retail DB and hash the result.

Uses tau-bench's real tool logic (the `invoke` functions that mutate the DB), so
the oracle is faithful to how tau-bench grades. tau_bench is imported lazily, so
importing this module has no cost until you actually replay.
"""
from __future__ import annotations
import copy
from functools import lru_cache
from typing import Any, Dict, List

from .action import Action
from .hashing import state_hash

RESPOND = "respond"  # tau-bench's non-tool "talk to user" action name


@lru_cache(maxsize=1)
def tools_map() -> Dict[str, Any]:
    """name -> tau_bench Tool class. Lazy import keeps this module light."""
    from tau_bench.envs.retail.tools import ALL_TOOLS

    return {t.get_info()["function"]["name"]: t for t in ALL_TOOLS}


def apply_action(data: Dict[str, Any], action: Action) -> str:
    """Mutate `data` in place per one action; return the observation string."""
    if action.name == RESPOND:
        return ""
    tm = tools_map()
    tool = tm.get(action.name)
    if tool is None:
        return f"Error: unknown action {action.name}"
    try:
        return tool.invoke(data=data, **action.kwargs)
    except Exception as e:  # mirrors tau-bench's own except-and-stringify
        return f"Error: {e}"


def replay(actions: List[Action], initial_data: Dict[str, Any]) -> Dict[str, Any]:
    """Replay the (write) actions on a deep copy of the DB; return the final state.
    Read-only actions are harmless; RESPOND is skipped, as in tau-bench grading."""
    data = copy.deepcopy(initial_data)
    for a in actions:
        apply_action(data, a)
    return data


def oracle_hash(actions: List[Action], initial_data: Dict[str, Any]) -> str:
    """The ground-truth state hash: replay the golden, hash the whole DB. This is
    exactly tau-bench's `calculate_reward` ground-truth computation."""
    return state_hash(replay(actions, initial_data))
