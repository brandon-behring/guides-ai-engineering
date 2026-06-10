"""Correctness tests for mini_agent. Run with `pytest`, or directly:
`python companion/tests/test_mini_agent.py` (no pytest needed)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mini_agent import (  # noqa: E402
    Action, Finish, Tool, run_agent,
    make_support_tools, support_policy, confused_policy, stuck_policy,
    run_supervisor, dependency_order, make_support_crew, sick_day_crew,
    triage_router,
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


def test_supervisor_routes_each_ticket_to_its_specialist():
    _fresh_world()
    trace = run_supervisor("Handle the queue: T1, T2, T3",
                           make_support_crew(), triage_router)
    assert trace.status == "complete"
    assert [h.worker for h in trace.handoffs] == [
        "policy_worker", "refund_worker", "frontdesk_worker"]
    # clean-context contract: each worker saw only its own ticket
    assert "T1" in trace.handoffs[0].goal and "T2" not in trace.handoffs[0].goal
    assert "R-18342" in trace.summary            # the refund actually happened


def test_failure_isolation_reroutes_to_human():
    _fresh_world()
    trace = run_supervisor("Handle the queue: T2",
                           sick_day_crew(), triage_router)
    assert trace.status == "complete"            # the QUEUE completed...
    assert trace.failed_handoffs                  # ...even though a worker didn't
    assert trace.failed_handoffs[0].trace.status == "loop_detected"
    assert trace.handoffs[-1].worker == "frontdesk_worker"
    assert "rerouted to a human" in trace.summary


def test_supervisor_handoff_budget_stops_livelock():
    _fresh_world()

    def relentless_router(task, handoffs):
        return ("delegate again", __import__("mini_agent").Assignment(
            "policy_worker", "Ticket T1: same thing again"))

    trace = run_supervisor("T1 forever", make_support_crew(),
                           relentless_router, max_handoffs=3)
    assert trace.status == "max_handoffs"
    assert len(trace.handoffs) == 3


def test_unknown_worker_is_a_record_not_a_crash():
    _fresh_world()
    calls = []

    def router(task, handoffs):
        if not handoffs:
            calls.append(1)
            return ("try the billing team", __import__("mini_agent").Assignment(
                "billing_worker", "Ticket T9"))
        return ("no such team — wrap up", Finish("done"))

    trace = run_supervisor("T9", make_support_crew(), router)
    assert trace.status == "complete"
    assert trace.handoffs[0].trace.status == "unknown_worker"
    assert "Available:" in trace.handoffs[0].trace.answer


def test_dependency_order_sorts_and_detects_deadlock():
    order = dependency_order({
        "content": [], "metadata": [], "compliance": [],
        "synthesizer": ["content", "metadata", "compliance"],
        "final": ["synthesizer"],
    })
    assert order.index("synthesizer") > order.index("content")
    assert order[-1] == "final"
    try:
        dependency_order({"a": ["b"], "b": ["a"]})
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "deadlock" in str(e)


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
