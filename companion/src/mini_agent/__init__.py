"""mini_agent — the build-your-own agent companion for the LLM App Engineering guide.

Deliberately minimal, stdlib-only (plus mini_rag for the retrieval tool),
**for learning, not production**. Module map:

- ``mini_agent.loop``  — the agent loop with its guards: Tool/Action/Finish/Step,
  a swappable Policy seat, run_agent -> AgentTrace (Ch 8).
- ``mini_agent.tools`` — a toy support desk: orders, a refund policy, three tools
  (one of them a gated WRITE), and scripted policies including broken ones (Ch 8).
- ``mini_agent.orchestrate`` — the supervisor pattern: Worker/Assignment/
  HandoffRecord, run_supervisor with failure isolation + a handoff budget,
  and dependency_order for deadlock prevention (Ch 9).
- ``mini_agent.crew`` — the worked support-desk crew: three specialists with
  least-privilege tools, a scripted triage router, and a sick-day variant (Ch 9).

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
from .orchestrate import (
    Worker,
    Assignment,
    HandoffRecord,
    OrchestraTrace,
    Router,
    run_supervisor,
    dependency_order,
)
from .crew import (
    TICKETS,
    make_support_crew,
    sick_day_crew,
    triage_router,
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
    "Worker",
    "Assignment",
    "HandoffRecord",
    "OrchestraTrace",
    "Router",
    "run_supervisor",
    "dependency_order",
    "TICKETS",
    "make_support_crew",
    "sick_day_crew",
    "triage_router",
]

__version__ = "0.1.0"
