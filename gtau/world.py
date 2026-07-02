"""A minimal live retail world the agent-under-test acts in.

Distinct from tau-bench's Env: no LLM user simulator (the instruction is self-
contained), so stepping the world makes no model API calls. The only model calls in
an episode come from the agent adapter (a CLI agent), which is the thing under test.
"""
from __future__ import annotations
import copy
from typing import Any, Dict, List

from .action import Action
from .replay import apply_action
from .hashing import state_hash

STOP = "stop"  # sentinel the agent emits to end the episode


class World:
    def __init__(self, data: Dict[str, Any], tools: Dict[str, Any]):
        self.data = copy.deepcopy(data)
        self.tools = tools
        self.executed: List[Action] = []
        self.done = False

    def step(self, action: Action) -> str:
        if action.name == STOP:
            self.done = True
            return "###STOP###"
        obs = apply_action(self.data, action, self.tools)
        self.executed.append(action)
        return obs

    def hash(self) -> str:
        return state_hash(self.data)
