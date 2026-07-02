"""Deterministic state hashing.

Copied verbatim (behavior-preserving) from tau-bench's `tau_bench/envs/base.py`
(MIT, Copyright 2024 Sierra) so the oracle we compute is bit-identical to the one
tau-bench's grader computes, without importing the litellm-carrying base module.
"""
from __future__ import annotations
from hashlib import sha256
from typing import Any


def to_hashable(item: Any) -> Any:
    if isinstance(item, dict):
        return tuple((k, to_hashable(v)) for k, v in sorted(item.items()))
    elif isinstance(item, list):
        return tuple(to_hashable(e) for e in item)
    elif isinstance(item, set):
        return tuple(sorted(to_hashable(e) for e in item))
    else:
        return item


def consistent_hash(value: Any) -> str:
    return sha256(str(value).encode("utf-8")).hexdigest()


def state_hash(data: Any) -> str:
    """Hash a whole DB state exactly as tau-bench does: to_hashable then sha256."""
    return consistent_hash(to_hashable(data))
