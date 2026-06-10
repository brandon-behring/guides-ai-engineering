"""Multi-agent orchestration — a supervisor, specialist workers, and the
coordination failures the architecture invites.

One loop became a team for exactly three legitimate reasons: specialization
(different workers, different tools and instructions), parallelism
(independent subtasks), and context decomposition (each worker reasons over a
CLEAN context — its own goal, not the queue's stew). The supervisor pattern is
the default topology: a router decomposes the task and assigns work; workers
never talk to each other; results come back for synthesis.

The price is coordination, and this module makes the bill visible:
- every handoff is recorded (``HandoffRecord``) with the full worker trace
  inside — debugging a team means reading the supervisor's lane *and* each
  worker's inner loop;
- a worker that fails does NOT fail the run — failure isolation means the
  router sees the failed status and can reroute (typically: to a human);
- the supervisor itself is budgeted (``max_handoffs``) — a router that keeps
  re-delegating is a livelock, the multi-agent flavor of Chapter 8's stuck loop;
- ``dependency_order`` topologically sorts workers whose inputs depend on each
  other and raises on cycles — deadlock prevention as ten lines of stdlib.

The router seat is scripted here for the same reason the policy seat was in
Chapter 8: every trace shown is honest. In production an LLM holds it.
Stdlib-only, **for learning, not production** — bridge to LangGraph
(supervisor + handoffs, typed state) and CrewAI (declarative fixed-role crews).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Union

from .loop import AgentTrace, Finish, Policy, Tool, run_agent


@dataclass(frozen=True)
class Worker:
    """A specialist: its own tools, its own policy, its own (clean) context.
    The description is what the router reads to decide who gets the work."""

    name: str
    description: str
    tools: list[Tool]
    policy: Policy
    max_steps: int = 8


@dataclass(frozen=True)
class Assignment:
    """The router's move: which worker, with what goal. The goal string is the
    ONLY context the worker receives — the handoff contract, made explicit."""

    worker: str
    goal: str


@dataclass(frozen=True)
class HandoffRecord:
    """One delegation, fully recorded: why, to whom, what they were told, and
    the worker's complete inner trace."""

    thought: str
    worker: str
    goal: str
    trace: AgentTrace


RouterDecision = tuple[str, Union[Assignment, Finish]]
Router = Callable[[str, list[HandoffRecord]], RouterDecision]


@dataclass
class OrchestraTrace:
    """The supervisor's lane: the task, every handoff (with worker traces
    inside), how it ended, and the synthesized summary."""

    task: str
    handoffs: list[HandoffRecord] = field(default_factory=list)
    status: str = "complete"
    summary: str = ""

    @property
    def failed_handoffs(self) -> list[HandoffRecord]:
        return [h for h in self.handoffs if h.trace.status != "complete"]


def run_supervisor(task: str, workers: list[Worker], router: Router,
                   max_handoffs: int = 6) -> OrchestraTrace:
    """The supervisor loop. The router sees the task and all completed
    handoffs (including failures) and returns the next Assignment or Finish.
    Unknown workers and failed workers become *records the router can read* —
    the same errors-as-observations stance as the single-agent loop —
    and ``max_handoffs`` is the livelock guard."""
    registry = {w.name: w for w in workers}
    trace = OrchestraTrace(task=task)

    for _ in range(max_handoffs):
        thought, decision = router(task, trace.handoffs)

        if isinstance(decision, Finish):
            trace.status = "complete"
            trace.summary = decision.answer
            return trace

        worker = registry.get(decision.worker)
        if worker is None:
            failed = AgentTrace(goal=decision.goal, status="unknown_worker",
                                answer=(f"No worker named '{decision.worker}'. "
                                        f"Available: {', '.join(sorted(registry))}."))
            trace.handoffs.append(HandoffRecord(thought, decision.worker,
                                                decision.goal, failed))
            continue

        inner = run_agent(decision.goal, worker.tools, worker.policy,
                          max_steps=worker.max_steps)
        trace.handoffs.append(HandoffRecord(thought, worker.name,
                                            decision.goal, inner))

    trace.status = "max_handoffs"
    trace.summary = ("Stopped: handoff budget exhausted before the task "
                     "completed. Partial results above.")
    return trace


def dependency_order(deps: dict[str, list[str]]) -> list[str]:
    """Topologically sort workers by their dependencies — the deadlock
    preventer. A waits on B while B waits on A is a cycle, and a cycle here
    is a ValueError at design time instead of two agents waiting forever at
    runtime."""
    in_degree = {name: 0 for name in deps}
    children: dict[str, list[str]] = {name: [] for name in deps}
    for name, parents in deps.items():
        for parent in parents:
            if parent not in deps:
                raise ValueError(f"unknown dependency '{parent}' for '{name}'")
            children[parent].append(name)
            in_degree[name] += 1

    queue = deque(sorted(n for n, d in in_degree.items() if d == 0))
    order: list[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for child in sorted(children[node]):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if len(order) != len(deps):
        cycle = sorted(set(deps) - set(order))
        raise ValueError(f"circular dependency (deadlock) among: {cycle}")
    return order
