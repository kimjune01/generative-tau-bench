"""Run one agent on one generated instance and score it.

Scoring mirrors tau-bench: success requires the final DB state to hash-match the
re-derived oracle, and every required output string to have been communicated.
No model API calls happen here except through the agent adapter.

CONSTRUCT-VALIDITY WARNING (see DESIGN.md Risks). A tau-bench `instruction` is the
*user simulator's* script, written in second person and carrying private,
conditional intent the agent is meant to ELICIT over dialogue ("if there is no
clicky keyboard, you'd rather only exchange the thermostat"). Handing it straight to
the agent (the default `user_sim=None` path here) leaks that intent. Such runs are an
EASIER task than tau-bench and are NOT comparable to tau-bench numbers:
`EpisodeResult.comparable` is False. A faithful run needs a `UserSim` (LLM or scripted)
that holds the instruction and answers only what the agent asks; the `user_sim` hook
is provided but no implementation ships yet.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Protocol

from .action import Action
from .generate import Instance
from .world import World
from .adapters.base import AgentAdapter, TaskView

RESPOND = "respond"
STOP = "stop"


class UserSim(Protocol):
    """Holds the private instruction; answers only what the agent asks. Implement to
    remove the intent leak and make runs tau-bench-comparable."""

    def opening(self) -> str: ...
    def reply(self, agent_message: str) -> str: ...


@dataclass
class EpisodeResult:
    success: bool
    reward: float
    r_state: bool
    r_outputs: bool
    agent_hash: str
    oracle: str
    comparable: bool = False  # True only when a UserSim mediated (no intent leak)
    error: Optional[str] = None
    executed: List[Action] = field(default_factory=list)
    transcript: List[dict] = field(default_factory=list)


def _outputs_present(required: List[str], messages: List[str]) -> bool:
    blob = " ".join(messages).lower().replace(",", "")
    return all(o.lower().replace(",", "") in blob for o in required)


def run_episode(
    agent: AgentAdapter,
    instance: Instance,
    tools: dict,
    max_steps: int = 30,
    user_sim: Optional[UserSim] = None,
) -> EpisodeResult:
    world = World(instance.data, tools)
    # With a UserSim, the agent must ELICIT intent and never sees the raw script.
    view = TaskView(
        instruction=user_sim.opening() if user_sim else instance.instruction,
        outputs=instance.outputs,
    )
    transcript: List[dict] = []
    messages: List[str] = []
    error: Optional[str] = None

    for _ in range(max_steps):
        try:
            action = agent.act(view, transcript)
        except Exception as e:  # a bad/garbled agent turn scores a failure, never crashes the run
            error = f"{type(e).__name__}: {e}"
            break
        if action.name == STOP:
            break
        if action.name == RESPOND:
            content = str(action.kwargs.get("content", ""))
            messages.append(content)
            reply = user_sim.reply(content) if user_sim else "(ok)"
            transcript.append({"role": "agent", "content": f"respond: {content}"})
            transcript.append({"role": "user", "content": reply})
            continue
        obs = world.step(action)
        transcript.append({"role": "agent", "content": f"{action.name}({action.kwargs})"})
        transcript.append({"role": "tool", "content": obs})

    r_state = world.hash() == instance.oracle
    r_outputs = _outputs_present(instance.outputs, messages)
    success = r_state and r_outputs and error is None
    return EpisodeResult(
        success=success,
        reward=1.0 if success else 0.0,
        r_state=r_state,
        r_outputs=r_outputs,
        agent_hash=world.hash(),
        oracle=instance.oracle,
        comparable=user_sim is not None,
        error=error,
        executed=world.executed,
        transcript=transcript,
    )
