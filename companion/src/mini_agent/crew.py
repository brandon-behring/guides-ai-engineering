"""The support-desk crew — a worked multi-agent example over Chapter 8's world.

Three specialists, each with only the tools its job needs (least privilege is
free reliability):

- ``policy_worker``  — answers policy questions; can read the policy, nothing else.
- ``refund_worker``  — Chapter 8's competent refund agent, tools and all.
- ``frontdesk_worker`` — no tools at all: it packages a warm human handoff.

The scripted ``triage_router`` reads a ticket queue, assigns each ticket to
the right specialist with a goal containing ONLY that ticket (the clean-context
contract), reroutes any failed handoff to the front desk (failure isolation),
and synthesizes a queue summary when everything is handled. ``sick_day_crew``
swaps the refund worker's policy for Chapter 8's stuck loop so the isolation
path actually runs — the failure is real, and so is the recovery.
"""

from __future__ import annotations

import re

from .loop import Action, Decision, Finish, Step
from .orchestrate import Assignment, HandoffRecord, RouterDecision, Worker
from .tools import make_support_tools, support_policy

TICKETS = [
    {"id": "T1", "text": "How long do I have to return something for a refund?",
     "kind": "policy"},
    {"id": "T2", "text": "Please refund order 18342, it arrived broken.",
     "kind": "refund"},
    {"id": "T3", "text": "This is the THIRD time I'm writing. I want a human. Now.",
     "kind": "human"},
]


def _policy_worker_policy(goal: str, steps: list[Step]) -> Decision:
    """Look the question up, answer from what came back."""
    if not steps:
        return ("A policy question — look it up rather than guessing.",
                Action("policy_lookup", {"question": goal}))
    return ("Answer with the retrieved policy, verbatim where possible.",
            Finish(f"Per our policy: {steps[-1].observation}"))


def _frontdesk_policy(goal: str, steps: list[Step]) -> Decision:
    """No tools: package a handoff a human can pick up cold."""
    return ("This needs a person; my job is a clean handoff, not a retry.",
            Finish(f"Escalated to a human agent with full context: {goal}"))


def make_support_crew() -> list[Worker]:
    tools = make_support_tools()
    read_only = [t for t in tools if not t.writes]
    policy_only = [t for t in tools if t.name == "policy_lookup"]
    return [
        Worker("policy_worker",
               "Answers policy questions. Read-only access to the policy.",
               policy_only, _policy_worker_policy),
        Worker("refund_worker",
               "Handles refund requests end-to-end: order facts, policy check, "
               "gated refund write.",
               tools, support_policy),
        Worker("frontdesk_worker",
               "Escalates to a human with a clean handoff summary. No tools.",
               [], _frontdesk_policy),
    ]


def sick_day_crew() -> list[Worker]:
    """Same crew, but the refund worker is having Chapter 8's bad day: it
    re-checks the order forever, and the loop guard ends it. Used to show
    failure isolation — the queue still gets handled."""
    from .tools import stuck_policy
    crew = make_support_crew()
    return [Worker(w.name, w.description, w.tools, stuck_policy, max_steps=6)
            if w.name == "refund_worker" else w for w in crew]


_TICKET_KIND = {"policy": "policy_worker", "refund": "refund_worker",
                "human": "frontdesk_worker"}


def triage_router(task: str, handoffs: list[HandoffRecord]) -> RouterDecision:
    """Scripted supervisor for the ticket queue: one handoff per ticket, in
    order; failed handoffs are rerouted to the front desk; finish with a
    synthesis once every ticket has a completed resolution."""
    ticket_ids = re.findall(r"\bT\d+\b", task)
    tickets = [t for t in TICKETS if t["id"] in ticket_ids]

    handled: dict[str, HandoffRecord] = {}
    for h in handoffs:
        tid = next((t["id"] for t in tickets if t["id"] in h.goal), None)
        if tid and h.trace.status == "complete":
            handled[tid] = h

    rerouted = {next((t["id"] for t in tickets if t["id"] in h.goal), "")
                for h in handoffs if h.worker == "frontdesk_worker"}

    for t in tickets:
        if t["id"] in handled:
            continue
        failed_before = any(t["id"] in h.goal and h.trace.status != "complete"
                            for h in handoffs)
        if failed_before and t["id"] not in rerouted:
            return (f"{t['id']}'s specialist failed ({_TICKET_KIND[t['kind']]}); "
                    "isolate the failure and route the ticket to a human instead.",
                    Assignment("frontdesk_worker",
                               f"Ticket {t['id']}: {t['text']} (automated handling "
                               "failed; needs a person)"))
        if not failed_before:
            return (f"{t['id']} is a {t['kind']} ticket — that's "
                    f"{_TICKET_KIND[t['kind']]}'s specialty. Hand it only this ticket.",
                    Assignment(_TICKET_KIND[t["kind"]],
                               f"Ticket {t['id']}: {t['text']}"))

    lines = []
    for t in tickets:
        h = handled.get(t["id"])
        lines.append(f"{t['id']}: {h.trace.answer if h else 'unresolved'}")
    failures = sum(1 for h in handoffs if h.trace.status != "complete")
    note = f" ({failures} specialist failure(s) rerouted to a human)" if failures else ""
    return ("Every ticket has a resolution — synthesize the queue summary.",
            Finish(f"Queue handled{note}. " + " | ".join(lines)))
