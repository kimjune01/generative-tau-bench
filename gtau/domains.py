"""A Domain is the entire per-benchmark adaptation the transformation needs.

Everything schema-specific lives here and nowhere else: the `id_collections`
descriptor (which dict-collections are keyed by ids), plus lazy loaders for the
data, the tasks, and the tool logic. Porting the method to a new database-shaped
benchmark = writing one of these. Its size is the portability metric.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Set


@dataclass
class Domain:
    name: str
    id_collections: Set[str]        # dict-field names whose keys are ids
    load_data: Callable[[], Dict[str, Any]]
    tasks: Callable[[], List[Any]]
    tools: Callable[[], Dict[str, Any]]  # name -> tau_bench Tool


def _tools_from(module_all_tools) -> Dict[str, Any]:
    return {t.get_info()["function"]["name"]: t for t in module_all_tools}


def _retail_data():
    from tau_bench.envs.retail.data import load_data
    return load_data()


def _retail_tasks():
    from tau_bench.envs.retail.tasks_test import TASKS_TEST
    return TASKS_TEST


def _retail_tools():
    from tau_bench.envs.retail.tools import ALL_TOOLS
    return _tools_from(ALL_TOOLS)


def _airline_data():
    from tau_bench.envs.airline.data import load_data
    return load_data()


def _airline_tasks():
    from tau_bench.envs.airline.tasks_test import TASKS
    return TASKS


def _airline_tools():
    from tau_bench.envs.airline.tools import ALL_TOOLS
    return _tools_from(ALL_TOOLS)


RETAIL = Domain(
    name="retail",
    id_collections={"users", "orders", "products", "payment_methods", "variants"},
    load_data=_retail_data,
    tasks=_retail_tasks,
    tools=_retail_tools,
)

AIRLINE = Domain(
    name="airline",
    id_collections={"users", "reservations", "flights", "payment_methods"},
    load_data=_airline_data,
    tasks=_airline_tasks,
    tools=_airline_tools,
)

DOMAINS: Dict[str, Domain] = {"retail": RETAIL, "airline": AIRLINE}
