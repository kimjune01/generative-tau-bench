"""Agent adapter interface.

An adapter turns some agent (an API model, or a CLI tool like `claude` / `codex`)
into something that emits one retail action at a time given the task and the
conversation so far. The eval loop drives it against a `World`.
"""
from __future__ import annotations
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List

from ..action import Action


@lru_cache(maxsize=1)
def tool_catalog() -> List[Dict[str, Any]]:
    """The retail tool schemas (OpenAI function-call format), from tau-bench."""
    from tau_bench.envs.retail.tools import ALL_TOOLS

    return [t.get_info() for t in ALL_TOOLS]


@lru_cache(maxsize=1)
def policy_wiki() -> str:
    from tau_bench.envs.retail.wiki import WIKI

    return WIKI


@dataclass
class TaskView:
    """Everything the agent-under-test is allowed to see for one instance."""
    instruction: str
    outputs: List[str]

    def system_prompt(self) -> str:
        tools = json.dumps(tool_catalog(), indent=2)
        return (
            "You are a customer-service agent operating a retail backend. Follow the "
            "policy exactly. You act by calling tools or messaging the user. On each "
            "of your turns, reply with EXACTLY ONE JSON object and nothing else, one of:\n"
            '  {"tool": "<tool_name>", "arguments": { ... }}\n'
            '  {"respond": "<message to the user>"}   // ask for or confirm information\n'
            '  {"stop": true}   // when the task is fully handled\n\n'
            f"POLICY:\n{policy_wiki()}\n\n"
            f"TOOLS (JSON schemas):\n{tools}\n"
        )


def _is_action_shaped(obj: Any) -> bool:
    return isinstance(obj, dict) and (
        obj.get("stop") is True
        or "respond" in obj
        or bool(obj.get("tool") or obj.get("name"))
    )


def parse_action(text: str) -> Action:
    """Extract the agent's action from raw stdout. We take the LAST action-shaped
    JSON object, so an agent that quotes the schema-laden prompt (dozens of tool
    schemas) before answering is not misparsed by grabbing the first `{...}`."""
    candidates = [o for o in _json_objects(text) if _is_action_shaped(o)]
    if not candidates:
        raise ValueError(f"no JSON action found in agent output: {text[:200]!r}")
    obj = candidates[-1]
    if obj.get("stop") is True:
        return Action(name="stop")
    if "respond" in obj:
        return Action(name="respond", kwargs={"content": str(obj["respond"])})
    name = obj.get("tool") or obj.get("name")
    return Action(name=name, kwargs=obj.get("arguments") or obj.get("kwargs") or {})


def _json_objects(text: str) -> List[Dict[str, Any]]:
    """All top-level `{...}` JSON objects in order."""
    out: List[Dict[str, Any]] = []
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        out.append(json.loads(text[start : i + 1]))
                    except json.JSONDecodeError:
                        pass
                    start = -1
    return out


class AgentAdapter(ABC):
    @abstractmethod
    def act(self, view: TaskView, transcript: List[Dict[str, str]]) -> Action:
        """Given the task and the running transcript (role/content dicts of prior
        actions and observations), return the next Action."""
        raise NotImplementedError
