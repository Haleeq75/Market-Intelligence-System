"""
app/agents/graph.py
────────────────────
LangGraph StateGraph definition.
Compiles the full Ear → Bull → Bear → Arbiter pipeline into
a single runnable graph.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.state import SwarmState
from app.agents.ear.agent import ear_node
from app.agents.bull.agent import bull_node
from app.agents.bear.agent import bear_node
from app.agents.arbiter.agent import arbiter_node
from app.core.logging import get_logger

log = get_logger(__name__)


def _should_continue(state: SwarmState) -> str:
    """
    Conditional edge: halt the graph early on error.
    Returns the name of the next node or END.
    """
    if state.get("status") == "error":
        log.warning(
            "swarm_pipeline_halted",
            ticker=state.get("ticker"),
            error=state.get("error"),
        )
        return END
    return "continue"


def build_swarm_graph() -> StateGraph:
    """
    Constructs the adversarial swarm pipeline:

    START → ear → [error check] → bull → [error check] → bear → [error check] → arbiter → END

    Sequential (not parallel) so each agent can read the previous agent's
    output from the shared SwarmState (A2A pattern).
    """
    graph = StateGraph(SwarmState)

    # Register nodes
    graph.add_node("ear", ear_node)
    graph.add_node("bull", bull_node)
    graph.add_node("bear", bear_node)
    graph.add_node("arbiter", arbiter_node)

    # Entry point
    graph.add_edge(START, "ear")

    # Conditional edges after each node: bail on error, continue otherwise
    graph.add_conditional_edges(
        "ear",
        _should_continue,
        {"continue": "bull", END: END},
    )
    graph.add_conditional_edges(
        "bull",
        _should_continue,
        {"continue": "bear", END: END},
    )
    graph.add_conditional_edges(
        "bear",
        _should_continue,
        {"continue": "arbiter", END: END},
    )
    graph.add_edge("arbiter", END)

    return graph


# Compiled graph singleton — thread-safe for async invocation
_compiled_graph = None


def get_compiled_graph():
    """Return the compiled LangGraph application (lazy singleton)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_swarm_graph().compile()
        log.info("swarm_graph_compiled")
    return _compiled_graph
