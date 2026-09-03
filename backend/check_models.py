"""
Lists all models available to GOOGLE_API_KEY and tests generateContent.
Uses the google-genai SDK (not google-generativeai).
"""
import os, sys

def load_env(path):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

load_env(os.path.join(os.path.dirname(__file__), '.env'))

api_key = os.environ.get("GOOGLE_API_KEY", "")
if not api_key:
    print("ERROR: GOOGLE_API_KEY not set in .env")
    sys.exit(1)

print(f"API key: {api_key[:12]}...")

from google import genai
client = genai.Client(api_key=api_key)

print("\n--- Available models (supports generateContent) ---")
generate_models = []
for m in client.models.list():
    methods = getattr(m, 'supported_generation_methods', []) or []
    supports_gen = (
        "generateContent" in methods
        or "GENERATE_CONTENT" in [str(x) for x in methods]
        or "GenerateContent" in [str(x) for x in methods]
    )
    if supports_gen:
        print(f"  GENERATE: {m.name}")
        generate_models.append(m.name)
    else:
        print(f"  other   : {m.name}  methods={methods}")

print(f"\n{len(generate_models)} models support generateContent")

# Test with a flash model
test_model = None
for pref in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash", "gemini-pro", "gemini"]:
    for m in generate_models:
        if pref in m.lower():
            test_model = m
            break
    if test_model:
        break
if not test_model and generate_models:
    test_model = generate_models[0]

if not test_model:
    print("No usable model found!")
    sys.exit(1)

print(f"\n--- Testing: {test_model} ---")
try:
    resp = client.models.generate_content(
        model=test_model,
        contents="Reply with exactly the word: GEMINI_OK"
    )
    text = resp.text.strip() if hasattr(resp, 'text') else str(resp)
    print(f"Response: {text}")
    print(f"\n✅ USE THIS MODEL IN llm.py: {test_model}")
except Exception as e:
    print(f"ERROR: {e}")
