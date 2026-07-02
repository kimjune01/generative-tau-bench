"""Drive a local CLI coding agent (`claude`, `codex`) as the agent-under-test.

Why CLI instead of an API model: the CLI tools carry their own auth and run
locally, so an episode needs no provider API keys and no litellm. The adapter shells
out once per agent turn, passing the task and transcript on the prompt, and parses a
single JSON action from stdout.

Nothing here is invoked at import time; running an episode is an explicit call.
"""
from __future__ import annotations
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List

from ..action import Action
from .base import AgentAdapter, TaskView, parse_action


@dataclass
class CLIAgentAdapter(AgentAdapter):
    name: str
    argv: List[str]                       # e.g. ["claude", "-p"]; prompt appended last
    prompt_via: str = "arg"               # "arg" (append prompt) or "stdin"
    timeout_s: int = 300
    env: Dict[str, str] = field(default_factory=dict)

    def act(self, view: TaskView, transcript: List[Dict[str, str]]) -> Action:
        prompt = self._build_prompt(view, transcript)
        out = self._run(prompt)
        return parse_action(out)

    def _build_prompt(self, view: TaskView, transcript: List[Dict[str, str]]) -> str:
        lines = [view.system_prompt(), "", f"TASK:\n{view.instruction}"]
        if view.outputs:
            lines.append(
                "\nYou must communicate these values to the user before stopping: "
                + ", ".join(view.outputs)
            )
        if transcript:
            lines.append("\nTRANSCRIPT SO FAR:")
            for turn in transcript:
                lines.append(f"[{turn['role']}] {turn['content']}")
        lines.append("\nReply with exactly one JSON action now.")
        return "\n".join(lines)

    def _run(self, prompt: str) -> str:
        import os

        run_env = {**os.environ, **self.env}
        if self.prompt_via == "stdin":
            proc = subprocess.run(
                self.argv, input=prompt, capture_output=True, text=True,
                timeout=self.timeout_s, env=run_env,
            )
        else:
            proc = subprocess.run(
                [*self.argv, prompt], capture_output=True, text=True,
                timeout=self.timeout_s, env=run_env,
            )
        if proc.returncode != 0:
            raise RuntimeError(
                f"{self.name} exited {proc.returncode}: {proc.stderr[:300]}"
            )
        return proc.stdout


def claude_adapter(timeout_s: int = 300) -> CLIAgentAdapter:
    # Claude Code headless: `claude -p "<prompt>"` prints the final text.
    return CLIAgentAdapter(name="claude", argv=["claude", "-p"], timeout_s=timeout_s)


def codex_adapter(timeout_s: int = 300) -> CLIAgentAdapter:
    # Codex non-interactive: `codex exec "<prompt>"` prints the final message.
    return CLIAgentAdapter(name="codex", argv=["codex", "exec"], timeout_s=timeout_s)
