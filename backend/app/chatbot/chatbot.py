"""
ORCA Fisherman Copilot — Main LangChain Entry Point

This is the independent LangChain conversational application that explains
ORCA's decisions, answers marine knowledge questions, and accesses live data.

Architecture:
    LangGraph decides → Supabase remembers → LangChain Copilot explains

The Copilot is NOT a LangGraph node. It never invokes, interrupts, or modifies
the Trip Planner workflow.

3 Layers:
    Layer 1 — Knowledge RAG (pgvector)
    Layer 2 — ORCA Context (read-only Supabase tools)
    Layer 3 — Live Data (weather/marine API tools)

Reference: 08_AI_ML_AGENTIC_ARCHITECTURE.md, Section 28
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.chatbot.prompts import COPILOT_SYSTEM_PROMPT, COPILOT_TOOL_INSTRUCTIONS
from app.chatbot.tools.orca_context_tools import ORCA_CONTEXT_TOOLS
from app.chatbot.tools.knowledge_tools import KNOWLEDGE_TOOLS
from app.chatbot.tools.live_data_tools import LIVE_DATA_TOOLS


# All tools available to the Copilot (all are read-only or retrieval-only)
ALL_COPILOT_TOOLS = ORCA_CONTEXT_TOOLS + KNOWLEDGE_TOOLS + LIVE_DATA_TOOLS


def get_copilot_chain(llm=None):
    """Create the ORCA Fisherman Copilot chain with tool calling.

    This creates a LangChain agent that:
    1. Receives the fisherman's message + conversation history
    2. Uses the system prompt to enforce safety boundaries
    3. Selects and calls the appropriate tools (ORCA context, knowledge, live data)
    4. Generates an evidence-grounded, multilingual response

    Args:
        llm: Optional LLM instance. If None, creates a default one.

    Returns:
        A runnable chain that accepts {"messages": [...]} and returns an AIMessage.

    Usage:
        chain = get_copilot_chain()
        result = chain.invoke({
            "messages": [
                HumanMessage(content="Why did ORCA say my trip is risky?")
            ]
        })
    """
    if llm is None:
        llm = _get_default_llm()

    # Bind all tools to the LLM
    llm_with_tools = llm.bind_tools(ALL_COPILOT_TOOLS) if llm else None

    # Build the prompt template
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=COPILOT_SYSTEM_PROMPT + "\n\n" + COPILOT_TOOL_INSTRUCTIONS),
        MessagesPlaceholder(variable_name="messages"),
    ])

    # Create the chain: prompt → LLM with tools
    if llm_with_tools:
        chain = prompt | llm_with_tools
    else:
        chain = None

    return chain


def get_copilot_agent(llm=None):
    """Create a full ReAct agent with tool execution loop.

    Unlike get_copilot_chain() which does a single LLM call,
    this creates an agent that can:
    1. Call a tool
    2. Read the tool result
    3. Call another tool or respond

    This is needed for multi-step reasoning like:
    "Why is my return risky?" →
        tool: get_risk_evidence(trip_id) →
        tool: get_weather_evidence(trip_id) →
        synthesize explanation

    Args:
        llm: Optional LLM instance.

    Returns:
        A LangGraph-powered agent executor.
    """
    # TODO: Implement with langgraph prebuilt agent when dependencies are installed
    #
    # from langgraph.prebuilt import create_react_agent
    #
    # if llm is None:
    #     llm = _get_default_llm()
    #
    # agent = create_react_agent(
    #     model=llm,
    #     tools=ALL_COPILOT_TOOLS,
    #     state_modifier=COPILOT_SYSTEM_PROMPT + "\n\n" + COPILOT_TOOL_INSTRUCTIONS,
    # )
    #
    # return agent

    return None


async def chat(
    user_message: str,
    conversation_history: list[dict] | None = None,
    trip_id: str | None = None,
    fisher_id: str | None = None,
) -> dict:
    """High-level chat interface for the ORCA Fisherman Copilot.

    This is the main function called by the FastAPI endpoint.

    Args:
        user_message: The fisherman's question.
        conversation_history: Previous messages in the conversation.
        trip_id: Optional trip ID for context-aware responses.
        fisher_id: Optional fisher ID for personalized responses.

    Returns:
        Dict with 'response' (the assistant's message) and 'tool_calls' (if any).
    """
    # Build message list
    messages = []

    # Add conversation history
    if conversation_history:
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

    # Add current message
    messages.append(HumanMessage(content=user_message))

    # Get the chain
    chain = get_copilot_chain()

    if chain is None:
        # Fallback when LLM is not configured
        return {
            "response": (
                "The ORCA Fisherman Copilot is not yet configured. "
                "Please set the GOOGLE_API_KEY environment variable."
            ),
            "tool_calls": [],
        }

    # Invoke the chain
    try:
        result = await chain.ainvoke({"messages": messages})

        return {
            "response": result.content,
            "tool_calls": getattr(result, "tool_calls", []),
        }
    except Exception as e:
        return {
            "response": f"I encountered an error: {str(e)}. Please try again.",
            "tool_calls": [],
        }


def _get_default_llm():
    """Create the default LLM instance for the Copilot.

    Uses Google Gemini via LangChain.

    Returns:
        LLM instance, or None if API key is not set.
    """
    import os

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("WARNING: GOOGLE_API_KEY not set. Copilot will return fallback responses.")
        return None

    # TODO: Uncomment when langchain_google_genai is installed
    #
    # from langchain_google_genai import ChatGoogleGenerativeAI
    #
    # return ChatGoogleGenerativeAI(
    #     model="gemini-2.0-flash",
    #     google_api_key=api_key,
    #     temperature=0.3,      # Low temperature for factual, grounded responses
    #     max_output_tokens=1024,
    # )

    return None
