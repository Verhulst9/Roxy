from typing import TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Model (Same as interaction graph)
llm = ChatOpenAI(
    model=os.getenv("MINIMAX_MODEL"),
    api_key=os.getenv("MINIMAX_API_KEY"),
    base_url=os.getenv("MINIMAX_API_BASE"),
    temperature=0.5, # Lower temperature for analytical tasks
)

def run_reflection(messages: List[BaseMessage]) -> str:
    """
    Analyzes a list of recent messages to extract high-level insights about the user.
    """
    if not messages:
        return None

    # 1. Format Conversation for Reflection
    conversation_text = ""
    for msg in messages:
        role = "User" if isinstance(msg, HumanMessage) else "Nakari"
        conversation_text += f"{role}: {msg.content}\n"

    # 2. Reflection Prompt
    # This guides the LLM to look for patterns, emotional states, or key facts.
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the subconscious reflection engine of an AI Assistant named Nakari. "
                   "Your goal is to analyze the recent conversation logs and extract ONE key insight about the user or the current context. "
                   "This insight will be stored in long-term memory to improve future interactions. "
                   "Focus on: User preferences, Emotional state, or Recurring topics. "
                   "Output ONLY the insight as a concise sentence."),
        ("human", f"Recent Conversation Logs:\n{conversation_text}\n\nExtract Key Insight:")
    ])

    # 3. Invoke Chain
    chain = prompt | llm
    
    print("🧠 Reflection Engine: Analyzing recent events...")
    try:
        result = chain.invoke({})
        insight = result.content.strip()
        print(f"💡 Reflection Insight: {insight}")
        return insight
    except Exception as e:
        print(f"❌ Reflection Error: {e}")
        return None
