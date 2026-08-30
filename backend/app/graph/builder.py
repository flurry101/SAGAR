"""
LangGraph Builder — Trip Planner Graph Construction

Builds the ORCA Trip Planner as a LangGraph StateGraph with:
- Planner → Geo → (Marine ∥ Weather) → Risk → Planner(synthesis) → Persist
- MemorySaver for MVP, swappable to PostgresSaver for production
- A final persist_results node that writes completed evidence to Supabase

Architecture:
    LangGraph decides → Supabase remembers → LangChain Copilot explains

NOTE: geo_node, marine_node, weather_node, risk_node are NOT implemented here.
      They belong to Members 3 and 4. This builder defines the graph structure
      and wires in their nodes once they provide the implementations.
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import OrcaState
from app.graph.routing import should_clarify, route_after_risk
from app.graph.nodes.planner import planner_intake, planner_synthesize

# ------------------------------------------------------------------
# Member 3 / Member 4 node imports — uncomment when they deliver
# ------------------------------------------------------------------
# from app.graph.nodes.geo import geo_node        # Member 3
# from app.graph.nodes.marine import marine_node   # Member 4
# from app.graph.nodes.weather import weather_node # Member 4
# from app.graph.nodes.risk import risk_node       # Member 3


# Temporary passthrough stubs so the graph can be defined without
# depending on other members' files. Replace with real imports above.
def _placeholder_node(state: OrcaState) -> OrcaState:
    """Passthrough — replace with real node from Member 3/4."""
    return state


def _persist_results(state: OrcaState) -> OrcaState:
    """Final node: persist completed agent evidence to Supabase.

    This is what enables the ORCA Fisherman Copilot to later explain
    decisions by reading completed, persisted evidence.

    Persists:
        - trip_context
        - trajectory
        - weather_observations (as weather_evidence)
        - marine_observations (as marine_evidence)
        - risk_evidence
        - advisory
        - agent_executions (execution history)
    """
    # TODO: Implement Supabase persistence via repositories
    # from app.repositories.trip_repo import persist_trip_evidence
    # await persist_trip_evidence(state)
    state["workflow_status"] = "PERSISTED"
    return state


def build_graph() -> StateGraph:
    """Construct the ORCA Trip Planner LangGraph.

    Graph flow:
        planner_intake
            → [needs_clarification?] → END (return clarification to user)
            → [validated] → geo
                → marine + weather (parallel)
                    → risk
                        → planner_synthesize
                            → persist_results
                                → END
    """
    graph = StateGraph(OrcaState)

    # --- Register nodes ---
    graph.add_node("planner_intake", planner_intake)
    graph.add_node("geo", _placeholder_node)              # Member 3
    graph.add_node("marine", _placeholder_node)            # Member 4
    graph.add_node("weather", _placeholder_node)           # Member 4
    graph.add_node("risk", _placeholder_node)              # Member 3
    graph.add_node("planner_synthesize", planner_synthesize)
    graph.add_node("persist_results", _persist_results)

    # --- Entry point ---
    graph.set_entry_point("planner_intake")

    # --- Edges ---
    # Planner intake: either clarify or proceed to geo
    graph.add_conditional_edges(
        "planner_intake",
        should_clarify,
        {
            "clarify": END,
            "proceed": "geo",
        },
    )

    # Geo → parallel Marine + Weather
    graph.add_edge("geo", "marine")
    graph.add_edge("geo", "weather")

    # Marine + Weather → Risk (both must complete)
    graph.add_edge("marine", "risk")
    graph.add_edge("weather", "risk")

    # Risk → route based on result
    graph.add_conditional_edges(
        "risk",
        route_after_risk,
        {
            "synthesize": "planner_synthesize",
            "insufficient": "planner_synthesize",
        },
    )

    # Planner synthesis → persist → END
    graph.add_edge("planner_synthesize", "persist_results")
    graph.add_edge("persist_results", END)

    return graph


def get_compiled_graph(checkpointer=None):
    """Return a compiled graph instance ready for invocation.

    Args:
        checkpointer: Optional checkpointer. Defaults to MemorySaver (MVP).
                      For production, pass PostgresSaver backed by Supabase.

    Usage:
        # MVP
        graph = get_compiled_graph()
        result = await graph.ainvoke(
            {"conversation_history": [{"role": "user", "content": msg}]},
            config={"configurable": {"thread_id": session_id}},
        )

        # Production (PostgresSaver)
        from langgraph.checkpoint.postgres import PostgresSaver
        import psycopg
        conn = psycopg.connect(settings.SUPABASE_DB_URL)
        graph = get_compiled_graph(checkpointer=PostgresSaver(conn))
    """
    if checkpointer is None:
        checkpointer = MemorySaver()

    return build_graph().compile(checkpointer=checkpointer)
