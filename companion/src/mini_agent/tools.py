"""A toy support desk for the agent to act on — tools, data, and policies.

The world: three orders, a refund policy, and three tools. ``order_status``
and ``policy_lookup`` are reads (safe to retry); ``start_refund`` is a WRITE —
it changes the world, so it's flagged, gated by the policy's eligibility
check, and returns a confirmation id like a real one would. ``policy_lookup``
is literally Chapter 2's retrieval reused: the RAG pipeline has become a tool
an agent can call.

The scripted policies are the "reasoning engine" stand-ins:
- ``support_policy`` — the competent one: check the order's facts, look up the
  relevant policy, and only then decide (refund / refuse / explain).
- ``confused_policy`` — calls a tool that doesn't exist first (a hallucinated
  tool call), reads the error observation, and recovers.
- ``stuck_policy`` — re-checks the order status forever; the loop guard ends it.

Hand-authored and deterministic on purpose: every trace in the guide is real
output of ``run_agent`` over these, not a transcript someone wrote to look good.
"""

from __future__ import annotations

import re

from mini_rag import top_k

from .loop import Action, Decision, Finish, Step, Tool

ORDERS = {
    "18342": {"item": "wireless keyboard", "category": "standard",
              "days_since_purchase": 12, "status": "delivered"},
    "20117": {"item": "$50 gift card", "category": "gift card",
              "days_since_purchase": 3, "status": "delivered"},
    "19026": {"item": "desk lamp", "category": "standard",
              "days_since_purchase": 45, "status": "delivered"},
}

SUPPORT_POLICY = [
    "You may request a refund within 30 days of purchase.",
    "Gift cards and final-sale items are non-refundable.",
    "Approved refunds are paid to the original payment method within 5 business days.",
    "Items marked as clearance may be exchanged for store credit instead.",
]


def order_status(order_id: str) -> str:
    """Look up one order. Read-only; returns a structured one-liner the
    policy can parse — or an error message it can act on."""
    order = ORDERS.get(order_id)
    if order is None:
        return (f"No order found with id '{order_id}'. "
                "Check the id and try again.")
    return (f"Order {order_id}: {order['item']} ({order['category']}), "
            f"{order['status']}, purchased {order['days_since_purchase']} days ago.")


def policy_lookup(question: str) -> str:
    """Retrieve the most relevant policy sentences — Chapter 2's lexical
    search, now wearing a tool's interface. Read-only."""
    hits = top_k(question, SUPPORT_POLICY, k=2)
    if not hits:
        return "No matching policy found."
    return " ".join(h.doc for h in hits)


_REFUNDS_STARTED: list[str] = []


def start_refund(order_id: str) -> str:
    """Initiate a refund — a WRITE. Idempotent on purpose: starting the same
    refund twice returns the same confirmation instead of paying twice."""
    if order_id not in ORDERS:
        return f"Cannot refund: no order with id '{order_id}'."
    if order_id in _REFUNDS_STARTED:
        return f"Refund already in progress for order {order_id} (confirmation R-{order_id})."
    _REFUNDS_STARTED.append(order_id)
    return f"Refund initiated for order {order_id}. Confirmation R-{order_id}."


def make_support_tools() -> list[Tool]:
    return [
        Tool("order_status",
             "Look up an order by id. Returns item, category, status, and "
             "days since purchase. Read-only. Use before any refund decision.",
             order_status),
        Tool("policy_lookup",
             "Search the refund policy. Returns the most relevant policy "
             "sentences. Read-only. Do NOT use for order data.",
             policy_lookup),
        Tool("start_refund",
             "Initiate a refund for an order id. WRITES: moves money. Only "
             "call after confirming eligibility (window and category).",
             start_refund, writes=True),
    ]


_ORDER_ID = re.compile(r"\b(\d{5})\b")
_DAYS = re.compile(r"purchased (\d+) days ago")


def support_policy(goal: str, steps: list[Step]) -> Decision:
    """The competent scripted policy: facts first, policy second, then the
    decision — and the write-tool only fires when both checks pass."""
    order_id = (_ORDER_ID.search(goal) or ["", "unknown"])[1] if _ORDER_ID.search(goal) else "unknown"

    if not steps:
        return ("A refund decision needs the order's facts first — what was "
                "bought, and when.",
                Action("order_status", {"order_id": order_id}))

    last = steps[-1]
    if last.action and last.action.tool == "order_status":
        if "gift card" in last.observation:
            return ("It's a gift card — before anything else, check what the "
                    "policy says about gift cards.",
                    Action("policy_lookup", {"question": "are gift cards refundable"}))
        return ("Got the purchase date. Now the policy: what's the refund window?",
                Action("policy_lookup", {"question": "refund window days after purchase"}))

    if last.action and last.action.tool == "policy_lookup":
        status_obs = next((s.observation for s in steps
                           if s.action and s.action.tool == "order_status"), "")
        if "gift card" in status_obs:
            return ("Policy is explicit: gift cards are non-refundable. Do NOT "
                    "call the refund tool; explain instead.",
                    Finish("I'm sorry — gift cards are non-refundable under our policy. "
                           "I haven't started a refund. Is there anything else I can check?"))
        days_m = _DAYS.search(status_obs)
        days = int(days_m[1]) if days_m else 999
        window_m = re.search(r"within (\d+) days", last.observation)
        window = int(window_m[1]) if window_m else 30
        if days <= window:
            return (f"Purchased {days} days ago, window is {window} — eligible. "
                    "Safe to start the refund.",
                    Action("start_refund", {"order_id": order_id}))
        return (f"Purchased {days} days ago — outside the {window}-day window. "
                "Refuse politely, with the reason.",
                Finish(f"Unfortunately this order is outside the {window}-day refund "
                       f"window ({days} days since purchase), so I can't start a "
                       "refund. Clearance items may qualify for store credit."))

    if last.action and last.action.tool == "start_refund":
        return ("Refund confirmed — report the confirmation id back.",
                Finish(f"Done! {last.observation} You'll see the money back on the "
                       "original payment method within 5 business days."))

    return ("Nothing left to do.", Finish("Task complete."))


def confused_policy(goal: str, steps: list[Step]) -> Decision:
    """Hallucinates a tool on its first move, then reads the error
    observation and recovers — the unknown-tool guard, exercised."""
    if not steps:
        return ("The warranty system will know about refunds.",
                Action("check_warranty", {"order_id": "18342"}))
    if steps[-1].observation.startswith("Tool error"):
        return ("No such tool — the error lists what IS available. The policy "
                "lookup is the right move.",
                Action("policy_lookup", {"question": "refund window"}))
    return ("Policy found; answer with it.",
            Finish(f"Per policy: {steps[-1].observation}"))


def stuck_policy(goal: str, steps: list[Step]) -> Decision:
    """Re-checks the same order forever — no progress, just spend. The loop
    guard exists for exactly this trace."""
    return ("Better check the order status (again).",
            Action("order_status", {"order_id": "18342"}))
