"""Correctness tests for mini_agent. Run with `pytest`, or directly:
`python companion/tests/test_mini_agent.py` (no pytest needed)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mini_agent import (  # noqa: E402
    Action, Finish, Tool, run_agent,
    make_support_tools, support_policy, confused_policy, stuck_policy,
)
import mini_agent.tools as agent_tools  # noqa: E402


def _fresh_world():
    agent_tools._REFUNDS_STARTED.clear()


def test_eligible_order_gets_refund_with_confirmation():
    _fresh_world()
    trace = run_agent("Customer asks: refund order 18342 please",
                      make_support_tools(), support_policy)
    assert trace.status == "complete"
    assert "R-18342" in trace.answer
    # facts and policy were checked BEFORE the write fired
    assert trace.tools_called == ["order_status", "policy_lookup", "start_refund"]


def test_gift_card_never_triggers_the_write_tool():
    _fresh_world()
    trace = run_agent("Customer asks: refund order 20117 (gift card)",
                      make_support_tools(), support_policy)
    assert trace.status == "complete"
    assert "non-refundable" in trace.answer
    assert "start_refund" not in trace.tools_called   # the gate held


def test_out_of_window_order_is_refused_with_reason():
    _fresh_world()
    trace = run_agent("Refund order 19026?", make_support_tools(), support_policy)
    assert trace.status == "complete"
    assert "start_refund" not in trace.tools_called
    assert "45 days" in trace.answer


def test_unknown_tool_is_an_observation_not_a_crash():
    _fresh_world()
    trace = run_agent("Refund order 18342", make_support_tools(), confused_policy)
    assert trace.status == "complete"
    first_obs = trace.steps[0].observation
    assert first_obs.startswith("Tool error: no tool named 'check_warranty'")
    assert "Available:" in first_obs                  # the model can recover from this
    assert trace.tools_called[1] == "policy_lookup"   # ...and it did


def test_loop_guard_aborts_repeated_actions():
    _fresh_world()
    trace = run_agent("Refund order 18342", make_support_tools(), stuck_policy,
                      max_steps=10)
    assert trace.status == "loop_detected"
    assert len(trace.steps) < 10                      # stopped before the budget


def test_step_budget_and_bounded_observations():
    _fresh_world()
    chatty = Tool("chatty", "returns a flood", lambda: "x" * 10_000)

    def chatty_policy(goal, steps):
        return ("more", Action("chatty", {}))

    trace = run_agent("flood", [chatty], chatty_policy, max_steps=2, loop_window=1)
    assert trace.status == "max_steps"
    assert all(len(s.observation) <= 520 for s in trace.steps)  # truncated


def test_refund_write_is_idempotent():
    _fresh_world()
    first = agent_tools.start_refund("18342")
    second = agent_tools.start_refund("18342")
    assert "initiated" in first.lower()
    assert "already in progress" in second.lower()
    assert "R-18342" in second                        # same confirmation, not a second payout


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
