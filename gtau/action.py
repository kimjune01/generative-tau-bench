"""A minimal action record, decoupled from tau_bench's own types so the re-key and
hashing layers stay import-light (no litellm/openai/anthropic pulled in)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Action:
    name: str
    kwargs: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_tau(cls, a: Any) -> "Action":
        """Convert a tau_bench.types.Action (has .name, .kwargs) into ours."""
        return cls(name=a.name, kwargs=dict(getattr(a, "kwargs", {}) or {}))
