"""
LangGraph Builder — Bounded-Autonomous Supervisor Architecture

Builds the ORCA Marine Intelligence Graph with:
- Supervisor → Safety Guard → Dynamic Routing
- Geo → (Marine ∥ Weather) → Risk → Post-Processing → Synthesis → Persist
- Knowledge-only queries skip the entire data pipeline

Architecture:
    USER
     ↓
    SUPERVISOR (intent + task decomposition)
     ↓
    SAFETY GUARD (enforce mandatory risk for trips)
     ↓
    DYNAMIC ROUTER
     ├── knowledge-only → Copilot/RAG → END
     ├── clarification → END
     └── operational → Geo → Marine+Weather → Risk
                        → Ocean Analytics → Route
                        → Visualization → Reporting
                        → Synthesis → Persist → END

CRITICAL SAFETY PRINCIPLE:
    The LLM/Supervisor can decide WHICH capabilities are needed.
    The LLM/Supervisor must NEVER decide the safety outcome.
    The deterministic Risk Engine retains full authority over safety decisions.
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.config import settings
from app.graph.state import OrcaState
from app.graph.routing import supervisor_router, post_risk_router

# --- Node imports ---
from app.graph.nodes.context_resolution import resolve_context
from app.graph.nodes.supervisor import supervisor_node
from app.graph.nodes.planner import planner_intake, planner_synthesize
from app.graph.nodes.geo import geo_node
from app.graph.nodes.marine import marine_node
from app.graph.nodes.weather import weather_node
from app.graph.nodes.risk import risk_node
from app.graph.nodes.ocean_analytics import ocean_analytics_node
from app.graph.nodes.route import route_node
from app.graph.nodes.visualization import visualization_node
from app.graph.nodes.reporting import reporting_node
from app.graph.nodes.translation import translation_node


def _knowledge_node(state: OrcaState) -> OrcaState:
    """Handle knowledge-only queries via the Copilot/RAG path.

    When the Supervisor determines only knowledge/copilot is needed,
    this node provides a contextual response using the LLM.
    """
    from datetime import datetime, timezone
    from app.core.llm import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage

    task_plan = state.get("task_plan", {})
    history = state.get("conversation_history", [])
    user_query = history[-1].get("content", "") if history else "I have a question."
    
    advisory = state.get("advisory", {})
    risk = state.get("risk_evidence", {})
    trip = state.get("trip_context", {})
    
    llm = get_llm()
    answer_text = "This is a knowledge question. Use the ORCA Copilot for detailed answers."
    
    if llm:
        sys_prompt = f"""You are SAGAR, the ORCA Copilot. The user is asking a conversational question about their maritime voyage or general knowledge.
Context about their current trip plan:
- Trip: {trip}
- Last Advisory: {advisory.get('recommendation_text', 'None')}
- Risk Evidence: {risk}

Answer the user's question concisely and professionally. If they are asking about their plan or why a decision was made, explain it using the context provided."""
        try:
            resp = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=user_query)])
            answer_text = resp.content
            if isinstance(answer_text, list):
                # Langchain sometimes returns a list of blocks for Gemini
                answer_text = "\n".join([str(b.get("text", "")) for b in answer_text if isinstance(b, dict) and "text" in b])
        except Exception as e:
            answer_text = f"Failed to generate response: {e}"

    return {
        "advisory": {
            "advisory_category": "KNOWLEDGE_RESPONSE",
            "recommendation_text": answer_text,
            "reason": f"Intent: {task_plan.get('intent', 'knowledge')}",
            "affected_phase": "",
            "affected_time": "",
            "affected_location": "",
            "vessel_context": "",
            "evidence_summary": "",
            "uncertainty_notes": "",
            "disclaimer": "ORCA provides decision support only. Follow official alerts from INCOIS and IMD.",
            "language": state.get("trip_context", {}).get("language", "en"),
        },
        "workflow_status": "KNOWLEDGE_RESPONSE",
        "agent_executions": [{
            "agent_name": "knowledge_router",
            "status": "completed",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "data_sources": [],
            "output_summary": "Answered contextual follow-up.",
        }]
    }


def _persist_results(state: OrcaState) -> OrcaState:
    """Final node: persist completed agent evidence to Supabase.

    Persists:
        - assessment (top-level record)
        - trip_context
        - trajectory
        - weather_observations (as weather_evidence)
        - marine_observations (as marine_evidence)
        - risk_evidence
        - advisory
        - report
        - agent_executions (execution history)

    CRITICAL: Persistence failure does NOT alter the risk decision.
    """
    updates = {}
    try:
        from app.repositories.assessment_repository import persist_assessment

        result = persist_assessment(state)
        updates["persistence_status"] = result.get("persistence_status", "unknown")

        if result.get("errors"):
            updates["errors"] = [{
                "node": "persist",
                "message": f"Partial persistence: {result['errors']}",
                "tables_written": result.get("tables_written", []),
            }]

    except Exception as e:
        updates["persistence_status"] = "failed"
        updates["errors"] = [{
            "node": "persist",
            "message": f"Persistence failed: {e}. Risk decision is NOT affected.",
        }]

    return updates


def _post_process_node(state: OrcaState) -> OrcaState:
    """Run post-risk optional processing: ocean analytics, route, visualization, reporting.

    Only runs capabilities that were requested by the Supervisor's TaskPlan.
    """
    task_plan = state.get("task_plan", {})
    caps = set(task_plan.get("required_capabilities", []))

    accumulated_updates = {}

    # Ocean Analytics
    if "ocean_analytics" in caps:
        updates = ocean_analytics_node(state)
        _merge_updates(accumulated_updates, updates)

    # Route Optimization
    if "route" in caps:
        updates = route_node(state)
        _merge_updates(accumulated_updates, updates)

    # Visualization
    if "visualization" in caps:
        updates = visualization_node(state)
        _merge_updates(accumulated_updates, updates)

    # Reporting
    if "reporting" in caps:
        updates = reporting_node(state)
        _merge_updates(accumulated_updates, updates)

    return accumulated_updates


def _merge_updates(accumulated: dict, updates: dict) -> None:
    """Merge node updates into accumulated result, handling list-append fields properly."""
    for key, value in updates.items():
        if key in ("agent_executions", "evidence_registry", "alerts", "errors"):
            # Accumulate list fields by extending
            if key not in accumulated:
                accumulated[key] = []
            accumulated[key].extend(value if isinstance(value, list) else [value])
        else:
            accumulated[key] = value


def build_graph() -> StateGraph:
    """Construct the ORCA Bounded-Autonomous Supervisor Graph.

    Graph flow:
        supervisor
            → [needs_clarification?] → END
            → [knowledge_only?] → knowledge_node → END
            → [operational] → geo
                → marine + weather (parallel)
                    → risk
                        → [post_process?] → post_process_node → planner_synthesize
        context_resolution
            → supervisor
                → [needs_clarification?] → END
                → [knowledge_only?] → knowledge_node → END
                → [operational] → geo
                    → marine + weather (parallel)
                        → risk
                            → [post_process?] → post_process_node → planner_synthesize
                            → [no post?] → planner_synthesize
                                → persist_results
                                    → END
    """
    graph = StateGraph(OrcaState)

    # --- Register all nodes ---
    graph.add_node("context_resolution", resolve_context)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("knowledge", _knowledge_node)
    graph.add_node("geo", geo_node)
    graph.add_node("marine", marine_node)
    graph.add_node("weather", weather_node)
    graph.add_node("risk", risk_node)
    graph.add_node("post_process", _post_process_node)
    graph.add_node("planner_synthesize", planner_synthesize)
    graph.add_node("translation", translation_node)
    graph.add_node("persist_results", _persist_results)

    # --- Entry point ---
    graph.add_edge(START, "context_resolution")
    graph.add_edge("context_resolution", "supervisor")

    # --- Supervisor routing ---
    graph.add_conditional_edges(
        "supervisor",
        supervisor_router,
        {
            "clarify": END,
            "knowledge": "knowledge",
            "proceed": "geo",
        },
    )

    # Knowledge → END
    graph.add_edge("knowledge", END)

    # Geo → parallel Marine + Weather
    graph.add_edge("geo", "marine")
    graph.add_edge("geo", "weather")

    # Marine + Weather → Risk (both must complete)
    graph.add_edge("marine", "risk")
    graph.add_edge("weather", "risk")

    # Risk → post-processing or synthesis
    graph.add_conditional_edges(
        "risk",
        post_risk_router,
        {
            "post_process": "post_process",
            "synthesize": "planner_synthesize",
        },
    )

    # Post-process → synthesis
    graph.add_edge("post_process", "planner_synthesize")

    # Synthesis → translation → persist → END
    graph.add_edge("planner_synthesize", "translation")
    graph.add_edge("translation", "persist_results")
    graph.add_edge("persist_results", END)

    return graph


# Global checkpointer instance for MemorySaver to persist state across FastAPI requests
_memory_saver_instance = None

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
    global _memory_saver_instance
    
    if checkpointer is None:
        import os
        supabase_url = getattr(settings, "SUPABASE_DB_URL", None) or os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL")

        if supabase_url:
            try:
                from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
                import psycopg
                from psycopg.rows import dict_row

                # Given time constraints, fallback to MemorySaver for ainvoke compatibility.
                print("WARNING: PostgresSaver is sync but endpoint is async. Falling back to MemorySaver to prevent NotImplementedError.")
                if _memory_saver_instance is None:
                    _memory_saver_instance = MemorySaver()
                checkpointer = _memory_saver_instance
            except ImportError:
                print("WARNING: psycopg or langgraph-checkpoint-postgres not installed. Falling back to MemorySaver.")
                if _memory_saver_instance is None:
                    _memory_saver_instance = MemorySaver()
                checkpointer = _memory_saver_instance
            except Exception as e:
                print(f"WARNING: Could not connect to Postgres checkpointer: {e}. Falling back to MemorySaver.")
                if _memory_saver_instance is None:
                    _memory_saver_instance = MemorySaver()
                checkpointer = _memory_saver_instance
        else:
            if _memory_saver_instance is None:
                _memory_saver_instance = MemorySaver()
            checkpointer = _memory_saver_instance

    return build_graph().compile(checkpointer=checkpointer)
