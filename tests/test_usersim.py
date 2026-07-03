"""The user-sim path in run_episode: intent stays with the sim, the episode ends on
###STOP###, and only sim-mediated runs are marked tau-bench-comparable.

Uses stub agents/sims (no subprocess, no model calls); CLIUserSim's prompt assembly
is tested directly, its transport is not.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from gtau.action import Action
from gtau.adapters.base import AgentAdapter, TaskView
from gtau.branch import RETAIL_KEYBOARD_EXCHANGE as SPEC, generate_branch_instance
from gtau.domains import RETAIL
from gtau.eval import run_episode
from gtau.usersim import CLIUserSim, STOP_MARKER, is_stop, user_system_prompt


@dataclass
class StubUserSim:
    """Replies from a fixed script, then STOPs."""
    script: List[str]
    i: int = 0

    def opening(self) -> str:
        return self.script[0]

    def reply(self, agent_message: str) -> str:
        self.i += 1
        return self.script[self.i] if self.i < len(self.script) else STOP_MARKER


@dataclass
class ScriptedAgent(AgentAdapter):
    """Emits a fixed action list; used to drive the loop deterministically."""
    actions: List[Action]
    seen_instructions: List[str] = field(default_factory=list)
    i: int = 0

    def act(self, view: TaskView, transcript: List[Dict[str, str]]) -> Action:
        self.seen_instructions.append(view.instruction)
        a = self.actions[min(self.i, len(self.actions) - 1)]
        self.i += 1
        return a


def _branch_instance(seed: int = 0):
    return generate_branch_instance(SPEC, seed)


def test_sim_holds_instruction_agent_sees_opening_only():
    inst = _branch_instance()
    sim = StubUserSim(script=["Hi, I want to exchange some items."])
    agent = ScriptedAgent(actions=[Action("stop")])
    run_episode(agent, inst, RETAIL.tools(), user_sim=sim)
    assert agent.seen_instructions == ["Hi, I want to exchange some items."]
    assert inst.instruction not in agent.seen_instructions[0]


def test_stop_marker_ends_episode():
    inst = _branch_instance()
    sim = StubUserSim(script=["opening"])  # first reply after opening is STOP
    talker = ScriptedAgent(actions=[Action("respond", {"content": "anything else?"})] * 10)
    res = run_episode(talker, inst, RETAIL.tools(), max_steps=10, user_sim=sim)
    # one respond turn, then the sim's STOP ends it — the agent never burns max_steps
    assert talker.i == 1
    assert res.transcript[-1]["role"] == "user"
    assert is_stop(res.transcript[-1]["content"])


def test_comparable_only_with_sim():
    inst = _branch_instance()
    stopper = ScriptedAgent(actions=[Action("stop")])
    leaked = run_episode(stopper, inst, RETAIL.tools())
    mediated = run_episode(
        ScriptedAgent(actions=[Action("stop")]), inst, RETAIL.tools(),
        user_sim=StubUserSim(script=["hello"]),
    )
    assert leaked.comparable is False
    assert mediated.comparable is True


def test_cli_usersim_prompt_carries_instruction_and_dialogue():
    sim = CLIUserSim(instruction="You want to exchange X. If unavailable, do Y.", argv=["true"])
    sim.history = [
        {"role": "agent", "content": "Hi! How can I help you today?"},
        {"role": "user", "content": "I want to exchange something."},
    ]
    prompt = sim._build_prompt()
    assert user_system_prompt(sim.instruction) in prompt
    assert "[agent] Hi! How can I help you today?" in prompt
    assert "[user] I want to exchange something." in prompt
    # the tau-bench rules ride along verbatim
    assert "Do not give away all the instruction at once" in prompt
