import asyncio
import logging
from app.graph.builder import get_compiled_graph

logging.basicConfig(level=logging.INFO)

async def test():
    print("Getting graph...")
    graph = get_compiled_graph()
    
    print("Invoking graph...")
    state = {
        "conversation_history": [{"role": "user", "content": "Planning trip from Malpe at 6 AM, 4 hours fishing, return at 4 PM"}],
        "trip_context": {"session_id": "test", "language": "en"},
        "vessel_profile": {"beam_width_m": 4.5, "cruising_speed_kmh": 20},
        "workflow_status": "RECEIVED"
    }
    
    import time
    t0 = time.monotonic()
    result = await graph.ainvoke(state, config={"configurable": {"thread_id": "test"}})
    t1 = time.monotonic()
    print(f"Finished in {t1-t0:.2f}s")

if __name__ == "__main__":
    asyncio.run(test())
