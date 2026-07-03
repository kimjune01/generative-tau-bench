"""User simulator implementations for the `UserSim` hook in eval.py.

The simulator, not the agent, holds the task instruction; the agent must elicit
intent over dialogue. This is what removes the answer-sheet leak flagged in
DESIGN.md (Risks) and makes an episode tau-bench-comparable (`comparable=True`).

`CLIUserSim` mirrors tau-bench's `LLMUserSimulationEnv` (tau-bench
`tau_bench/envs/user.py`) — same system prompt verbatim, same opening exchange,
same `###STOP###` termination convention — but drives a local CLI model
(`claude -p`, `codex exec`) instead of litellm, consistent with the repo's
no-API-key CLI-agent choice. Comparability to tau-bench numbers therefore rests on
the prompt being tau-bench's, not on the transport.
"""
from __future__ import annotations
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List

STOP_MARKER = "###STOP###"

# Verbatim from tau-bench LLMUserSimulationEnv.build_system_prompt (MIT, Sierra),
# so a gtau episode poses the same elicitation task tau-bench poses.
_TAU_BENCH_RULES = """
Rules:
- Just generate one line at a time to simulate the user's message.
- Do not give away all the instruction at once. Only provide the information that is necessary for the current step.
- Do not hallucinate information that is not provided in the instruction. For example, if the agent asks for the order id but it is not mentioned in the instruction, do not make up an order id, just say you do not remember or have it.
- If the instruction goal is satisified, generate '###STOP###' as a standalone message without anything else to end the conversation.
- Do not repeat the exact instruction in the conversation. Instead, use your own words to convey the same information.
- Try to make the conversation as natural as possible, and stick to the personalities in the instruction."""


def user_system_prompt(instruction: str) -> str:
    return f"You are a user interacting with an agent.\n\nInstruction: {instruction}\n\n{_TAU_BENCH_RULES}"


@dataclass
class CLIUserSim:
    """Simulate the user with a local CLI model, one subprocess call per turn.

    The full dialogue rides on the prompt each turn (the CLI is stateless), so the
    per-turn cost grows with transcript length; tau-bench episodes are short enough
    that this stays well under any context limit.
    """
    instruction: str
    argv: List[str]                     # e.g. ["claude", "-p", "--model", "haiku"]
    timeout_s: int = 120
    history: List[Dict[str, str]] = field(default_factory=list, repr=False)

    def opening(self) -> str:
        # tau-bench opens with the agent's canned greeting, then the user speaks.
        return self.reply("Hi! How can I help you today?")

    def reply(self, agent_message: str) -> str:
        self.history.append({"role": "agent", "content": agent_message})
        out = self._run(self._build_prompt()).strip()
        # keep the marker standalone-detectable even if the model pads around it
        line = out.splitlines()[0].strip() if out else ""
        self.history.append({"role": "user", "content": line})
        return line

    def _build_prompt(self) -> str:
        lines = [user_system_prompt(self.instruction), "", "DIALOGUE SO FAR:"]
        for turn in self.history:
            lines.append(f"[{turn['role']}] {turn['content']}")
        lines.append("\nReply with the user's next single-line message now.")
        return "\n".join(lines)

    def _run(self, prompt: str) -> str:
        proc = subprocess.run(
            [*self.argv, prompt], capture_output=True, text=True, timeout=self.timeout_s
        )
        if proc.returncode != 0:
            raise RuntimeError(f"user-sim CLI failed ({proc.returncode}): {proc.stderr[:200]}")
        return proc.stdout


def is_stop(user_message: str) -> bool:
    return STOP_MARKER in user_message
