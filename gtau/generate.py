"""(base task, seed) -> a fresh, self-contained instance with a re-derived oracle.

For the MVP a "class" is an existing tau-bench retail task; generation is seeded
re-keying of it. Structural (constraint-aware) class generation is future work; see
DESIGN.md. tau_bench is imported lazily.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .action import Action
from .rekey import rekey_instance
from .replay import oracle_hash


@dataclass
class Instance:
    seed: int
    data: Dict[str, Any]           # the fresh initial DB
    golden: List[Action]           # the re-keyed golden program
    instruction: str               # the re-keyed task instruction (self-contained)
    outputs: List[str]             # required info the agent must communicate
    oracle: str                    # ground-truth final-state hash (re-derived)
    mapping: Dict[str, str] = field(default_factory=dict, repr=False)


def _base_retail_data() -> Dict[str, Any]:
    from tau_bench.envs.retail.data import load_data

    return load_data()


def _base_retail_tasks() -> List[Any]:
    from tau_bench.envs.retail.tasks_test import TASKS_TEST

    return TASKS_TEST


def generate_from_task(base_task: Any, seed: int, base_data: Dict[str, Any] | None = None) -> Instance:
    """Re-key a single base task into a fresh instance. `base_task` is a
    tau_bench.types.Task (has .instruction, .actions, .outputs)."""
    data = base_data if base_data is not None else _base_retail_data()
    golden = [Action.from_tau(a) for a in base_task.actions]
    instruction = base_task.instruction
    outputs = list(getattr(base_task, "outputs", []) or [])

    new_data, new_golden, new_instr, new_outputs, mapping = rekey_instance(
        data, golden, instruction, outputs, seed
    )
    return Instance(
        seed=seed,
        data=new_data,
        golden=new_golden,
        instruction=new_instr,
        outputs=new_outputs,
        oracle=oracle_hash(new_golden, new_data),
        mapping=mapping,
    )


def generate(task_index: int, seed: int) -> Instance:
    """Convenience: pick retail test task `task_index`, regenerate at `seed`."""
    tasks = _base_retail_tasks()
    return generate_from_task(tasks[task_index], seed)
