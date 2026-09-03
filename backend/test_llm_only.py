"""
Step 4: Test ONLY the LLM, not the full pipeline.
Sends a simple message and checks if Gemini responds directly.
"""
import os, sys, logging

logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')

def load_env(path):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line: continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

load_env(os.path.join(os.path.dirname(__file__), '.env'))

# Import the actual LLM class from the backend
sys.path.insert(0, os.path.dirname(__file__))
from app.core.llm import ResilientLLM
from langchain_core.messages import HumanMessage

import time

llm = ResilientLLM()

print(f"\nConfigured model: gemini-3.1-flash-lite")
print("Sending: 'Hello. Reply with exactly: GEMINI_OK'")
print("-" * 50)

t0 = time.monotonic()
result = llm.invoke([HumanMessage(content="Hello. Reply with exactly: GEMINI_OK")])
t1 = time.monotonic()

print(f"Response: {result.content[:200]}")
print(f"Time: {t1-t0:.2f}s")

if "GEMINI_OK" in result.content:
    print("\n✅ GEMINI responded correctly — primary LLM is working")
else:
    print("\n⚠️  Response doesn't contain GEMINI_OK — may be fallback/mock")
