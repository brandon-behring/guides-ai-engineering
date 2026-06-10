"""The agent loop — observe, think, act, and the guards that make it shippable.

An agent is a loop in which a model decides what happens next: read the state,
think, pick a tool (or finish), observe the result, repeat. Of the five
components every agent has — reasoning engine, tools, memory/state,
orchestration, guards — this module makes four of them real code. The fifth,
the reasoning engine, is a swappable ``policy`` callable. The guide's policies
are deliberately **scripted** (deterministic rules, no model) so every trace
shown is honest and reproducible; in production an LLM holds that seat via
tool/function calling, and *everything else in this file stays*.

The guards are the point. An unguarded loop with a stochastic decision-maker
will eventually: repeat itself forever (loop detection), call tools that don't
exist (surface the error as an observation — the model can read it), blow the
context (bounded observations), or run up a bill (step budget). Each guard
exists because its failure mode is routine, not exotic.

Stdlib-only, **for learning, not production** — bridge to tool/function
calling on any major API, agent frameworks (LangGraph et al.), and MCP as the
standard protocol layer between agents and tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Union


@dataclass(frozen=True)
class Tool:
    """The contract between the loop and an external capability. ``writes``
    flags tools with side effects — the ones that deserve gates, confirmation,
    and audit logs, because a read can be wrong for free and a write can't."""

    name: str
    description: str
    fn: Callable[..., str]
    writes: bool = False


@dataclass(frozen=True)
class Action:
    """A tool invocation the policy chose: which tool, with which arguments."""

    tool: str
    args: dict


@dataclass(frozen=True)
class Finish:
    """The policy's terminal move: stop looping and answer."""

    answer: str


@dataclass(frozen=True)
class Step:
    """One turn of the loop, fully recorded: the thought (why), the action
    (what), and the observation (what came back). The list of Steps IS the
    agent's working memory — and the debugging surface."""

    thought: str
    action: Action | None
    observation: str


Decision = tuple[str, Union[Action, Finish]]
Policy = Callable[[str, list[Step]], Decision]


@dataclass
class AgentTrace:
    """Everything one run did: the goal, every step, how it ended
    (``complete`` | ``max_steps`` | ``loop_detected``), and the answer."""

    goal: str
    steps: list[Step] = field(default_factory=list)
    status: str = "complete"
    answer: str = ""

    @property
    def tools_called(self) -> list[str]:
        return [s.action.tool for s in self.steps if s.action]


def _signature(action: Action) -> str:
    return action.tool + "|" + repr(sorted(action.args.items()))


def run_agent(goal: str, tools: list[Tool], policy: Policy,
              max_steps: int = 8, loop_window: int = 4,
              max_obs_chars: int = 500) -> AgentTrace:
    """Run the loop with its guards. The policy sees the goal and the full
    step history (its memory) and returns (thought, Action | Finish).

    Guards, in the order they fire:
    - **Finish** — the policy says it's done; status ``complete``.
    - **Loop detection** — the same (tool, args) appearing twice in the recent
      window aborts with ``loop_detected``: progress isn't happening, and
      every further step costs money.
    - **Unknown tool** — not an exception but an *observation* ("no tool named
      X; available: ..."), because the policy can read it and recover; a
      hallucinated tool call is a routine event, not a crash.
    - **Tool errors** — caught and surfaced as observations the same way.
    - **Bounded observations** — truncated to ``max_obs_chars`` so one chatty
      tool can't flood the working memory.
    - **Step budget** — the loop never runs more than ``max_steps``; status
      ``max_steps`` returns whatever partial progress exists.
    """
    registry = {t.name: t for t in tools}
    trace = AgentTrace(goal=goal)
    recent: list[str] = []

    for _ in range(max_steps):
        thought, decision = policy(goal, trace.steps)

        if isinstance(decision, Finish):
            trace.steps.append(Step(thought, None, "(finished)"))
            trace.status = "complete"
            trace.answer = decision.answer
            return trace

        sig = _signature(decision)
        if recent.count(sig) >= 2:
            trace.steps.append(Step(thought, decision, "(aborted: loop detected)"))
            trace.status = "loop_detected"
            trace.answer = "Aborted: the agent repeated the same action without progress."
            return trace
        recent.append(sig)
        if len(recent) > loop_window:
            recent.pop(0)

        tool = registry.get(decision.tool)
        if tool is None:
            observation = (f"Tool error: no tool named '{decision.tool}'. "
                           f"Available: {', '.join(sorted(registry))}.")
        else:
            try:
                observation = str(tool.fn(**decision.args))
            except Exception as e:  # surfaced, not raised — the policy can react
                observation = f"Tool error: {type(e).__name__}: {e}"
        if len(observation) > max_obs_chars:
            observation = observation[:max_obs_chars] + " …[truncated]"

        trace.steps.append(Step(thought, decision, observation))

    trace.status = "max_steps"
    trace.answer = "Stopped: step budget exhausted before the task completed."
    return trace
