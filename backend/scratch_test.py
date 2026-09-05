import os
import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import app.graph.state

load_dotenv()
try:
    llm = ChatGroq(model='qwen/qwen3.8-27b', temperature=0.1)
    system_prompt = f"""You are the ORCA Supervisor Agent.
Your job is to analyze the user's natural language request and output a structured task plan.

AVAILABLE CAPABILITIES:
{json.dumps(app.graph.state.APPROVED_CAPABILITIES)}

INTENT TIERS:
1. "conversational": Simple chat, greeting, thanks. (Capabilities: [])
2. "informational": General questions, or follow-up questions asking for reasons/explanations (e.g. "What is SST?", "Why is it dangerous?", "What is the reason I can't go to sea?"). (Capabilities: ["knowledge"])
3. "operational": Search or planning (e.g. "Find PFZ near Malpe"). (Capabilities: ["marine", "geo", "visualization"])
4. "safety_critical": Any new voyage, route, or safety assessment (e.g. "Is it safe to go fishing tomorrow?", "Plan a trip to X"). (Capabilities: ["geo", "weather", "marine", "risk", "visualization", "reporting"])

Respond ONLY with valid JSON in this exact schema:
```json
{{
  "intent": "conversational" | "informational" | "operational" | "safety_critical",
  "required_capabilities": ["list", "of", "capabilities"],
  "priority": "safety" | "information",
  "requires_safety_assessment": boolean,
  "requires_route": boolean,
  "requires_visualization": boolean,
  "requires_report": boolean,
  "clarification_required": boolean,
  "clarification_question": "string or null",
  "reasoning_summary": "string explaining capability selection",
  "extracted_origin": "string or null",
  "extracted_departure_time": "string (e.g. '5 AM', 'tomorrow'). Assume IST timezone. or null",
  "extracted_beam_width": number or null,
  "extracted_cruising_speed_kmh": number or null,
  "extracted_language": "en" | "hi" | "kn" | "ta" | "ml" | "or" | "gu" | "mr" | "te" | "bn"
}}
```"""
    user_message = "Planning trip from Rameswaram to Gulf of Mannar leaving at 4 AM and returning at 1 PM"
    resp = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_message)])
    print('RESPONSE:')
    print(resp.content)
except Exception as e:
    print('ERROR:')
    print(e)
