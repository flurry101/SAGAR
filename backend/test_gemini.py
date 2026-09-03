from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import os
import sys

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    from app.config import settings
    api_key = settings.GOOGLE_API_KEY

try:
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", google_api_key=api_key)
    res = llm.invoke([HumanMessage(content="Hello")])
    print("Success:", res.content)
except Exception as e:
    print("Error with 3.1-flash-lite:", e)

try:
    llm2 = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
    res2 = llm2.invoke([HumanMessage(content="Hello")])
    print("Success with 1.5-flash:", res2.content)
except Exception as e:
    print("Error with 1.5-flash:", e)
