"""Replay a golden action program against a tool-world DB and hash the result.

Uses tau-bench's real tool logic (the `invoke` functions that mutate the DB), so the
oracle is faithful to how tau-bench grades. The tool map is passed in (from a Domain),
so this module is schema-agnostic: nothing here names retail or airline.
"""
from __future__ import annotations
import copy
from typing import Any, Dict, List

from .action import Action
from .hashing import state_hash

RESPOND = "respond"  # tau-bench's non-tool "talk to user" action name


def apply_action(data: Dict[str, Any], action: Action, tools: Dict[str, Any]) -> str:
    """Mutate `data` in place per one action; return the observation string."""
    if action.name == RESPOND:
        return ""
    tool = tools.get(action.name)
    if tool is None:
        return f"Error: unknown action {action.name}"
    try:
        return tool.invoke(data=data, **action.kwargs)
    except Exception as e:  # mirrors tau-bench's own except-and-stringify
        return f"Error: {e}"


def replay(actions: List[Action], initial_data: Dict[str, Any], tools: Dict[str, Any]) -> Dict[str, Any]:
    """Replay the (write) actions on a deep copy of the DB; return the final state.
    Read-only actions are harmless; RESPOND is skipped, as in tau-bench grading."""
    data = copy.deepcopy(initial_data)
    for a in actions:
        apply_action(data, a, tools)
    return data


def oracle_hash(actions: List[Action], initial_data: Dict[str, Any], tools: Dict[str, Any]) -> str:
    """The ground-truth state hash: replay the golden, hash the whole DB. This is
    exactly tau-bench's `calculate_reward` ground-truth computation."""
    return state_hash(replay(actions, initial_data, tools))
