import asyncio
import json
import uuid
from app.graph.builder import get_compiled_graph

async def run_multiturn():
    graph = get_compiled_graph()
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    print(f"\n--- SESSION: {session_id} ---")

    # Turn 1
    msg1 = "I want to go fishing from Mangalore tomorrow."
    print(f"\nUSER (Turn 1): {msg1}")
    state1 = {
        "conversation_history": [{"role": "user", "content": msg1}],
        "trip_context": {"fisher_id": "test_user"}
    }
    res1 = await graph.ainvoke(state1, config=config)
    print(f"\nSUPERVISOR INTENT: {res1.get('task_plan', {}).get('intent')}")
    print(f"CAPABILITIES: {res1.get('task_plan', {}).get('required_capabilities')}")
    print(f"TRIP CONTEXT: {json.dumps(res1.get('trip_context', {}), indent=2)}")
    print(f"\nADVISORY (Turn 1): {json.dumps(res1.get('advisory', {}), indent=2)}")

    # Turn 2
    msg2 = "What about 6 PM?"
    print(f"\nUSER (Turn 2): {msg2}")
    state2 = {
        "conversation_history": [{"role": "user", "content": msg2}],
    }
    res2 = await graph.ainvoke(state2, config=config)
    print(f"\nRESOLVED QUERY: {res2.get('resolved_query')}")
    print(f"TRIP CONTEXT (Updated): {json.dumps(res2.get('trip_context', {}), indent=2)}")
    print(f"\nADVISORY (Turn 2): {json.dumps(res2.get('advisory', {}), indent=2)}")

    # Turn 3
    msg3 = "Hello"
    print(f"\nUSER (Turn 3): {msg3}")
    state3 = {
        "conversation_history": [{"role": "user", "content": msg3}],
    }
    res3 = await graph.ainvoke(state3, config=config)
    print(f"\nRESOLVED QUERY: {res3.get('resolved_query')}")
    print(f"SUPERVISOR INTENT: {res3.get('task_plan', {}).get('intent')}")
    
    print("\n--- TEST COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(run_multiturn())
