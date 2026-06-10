"""mini_agent — the build-your-own agent companion for the LLM App Engineering guide.

Deliberately minimal, stdlib-only (plus mini_rag for the retrieval tool),
**for learning, not production**. Module map:

- ``mini_agent.loop``  — the agent loop with its guards: Tool/Action/Finish/Step,
  a swappable Policy seat, run_agent -> AgentTrace (Ch 8).
- ``mini_agent.tools`` — a toy support desk: orders, a refund policy, three tools
  (one of them a gated WRITE), and scripted policies including broken ones (Ch 8).

The reasoning seat is scripted here so every trace is honest; production puts
an LLM in it via tool/function calling. Agent *evaluation* lives in
``mini_eval.agent`` (the Evaluation guide): mechanism here, measurement there.
"""

from .loop import (
    Tool,
    Action,
    Finish,
    Step,
    AgentTrace,
    Policy,
    Decision,
    run_agent,
)
from .tools import (
    ORDERS,
    SUPPORT_POLICY,
    order_status,
    policy_lookup,
    start_refund,
    make_support_tools,
    support_policy,
    confused_policy,
    stuck_policy,
)

__all__ = [
    "Tool",
    "Action",
    "Finish",
    "Step",
    "AgentTrace",
    "Policy",
    "Decision",
    "run_agent",
    "ORDERS",
    "SUPPORT_POLICY",
    "order_status",
    "policy_lookup",
    "start_refund",
    "make_support_tools",
    "support_policy",
    "confused_policy",
    "stuck_policy",
]

__version__ = "0.1.0"
