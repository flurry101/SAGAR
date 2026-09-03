import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

async def main():
    llm = get_llm()
    messages = [
        SystemMessage(content="You are an intent classification and task decomposition assistant."),
        HumanMessage(content="Hello")
    ]
    
    # Try calling the primary LLM directly to see the exact error
    try:
        print("Calling Primary LLM...")
        resp = llm.primary_llm.invoke(messages)
        print("Success:")
        print(resp)
    except Exception as e:
        print(f"Primary LLM Exception: {type(e).__name__}")
        print(f"Error details: {e}")
        
    print("\nCalling Resilient LLM (with fallback)...")
    resp = llm.invoke(messages)
    print("Fallback response:")
    print(resp.content)

if __name__ == "__main__":
    asyncio.run(main())
