"""(base task, seed) -> a fresh, self-contained instance with a re-derived oracle.

A "class" here is an existing tau-bench task; generation is seeded re-keying of it,
parameterized by a Domain (the per-benchmark descriptor). Structural (constraint-
aware) class generation is future work; see DESIGN.md.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .action import Action
from .rekey import rekey_instance
from .replay import oracle_hash
from .domains import Domain, DOMAINS


@dataclass
class Instance:
    seed: int
    data: Dict[str, Any]           # the fresh initial DB
    golden: List[Action]           # the re-keyed golden program
    instruction: str               # the re-keyed task instruction (self-contained)
    outputs: List[str]             # required info the agent must communicate
    oracle: str                    # ground-truth final-state hash (re-derived)
    domain: str = "retail"
    mapping: Dict[str, str] = field(default_factory=dict, repr=False)


def _resolve(domain: Union[str, Domain]) -> Domain:
    return DOMAINS[domain] if isinstance(domain, str) else domain


def generate_from_task(
    base_task: Any,
    seed: int,
    domain: Union[str, Domain],
    base_data: Optional[Dict[str, Any]] = None,
) -> Instance:
    """Re-key one base task into a fresh instance. `base_task` is a tau_bench.types.Task
    (has .instruction, .actions, .outputs)."""
    dom = _resolve(domain)
    data = base_data if base_data is not None else dom.load_data()
    golden = [Action.from_tau(a) for a in base_task.actions]
    instruction = base_task.instruction
    outputs = list(getattr(base_task, "outputs", []) or [])

    new_data, new_golden, new_instr, new_outputs, mapping = rekey_instance(
        data, golden, instruction, outputs, seed, dom.id_collections
    )
    return Instance(
        seed=seed,
        data=new_data,
        golden=new_golden,
        instruction=new_instr,
        outputs=new_outputs,
        oracle=oracle_hash(new_golden, new_data, dom.tools()),
        domain=dom.name,
        mapping=mapping,
    )


def generate(domain: Union[str, Domain], task_index: int, seed: int) -> Instance:
    """Convenience: pick test task `task_index` from `domain`, regenerate at `seed`."""
    dom = _resolve(domain)
    return generate_from_task(dom.tasks()[task_index], seed, dom)
