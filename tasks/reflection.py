from .app import app
from context import context_manager
from llm.reflection import run_reflection
from langchain_core.messages import HumanMessage, AIMessage

@app.task(queue="low_priority")
def consolidate_memory():
    """
    Periodic task to consolidate memory and find patterns.
    """
    print("Consolidating memory...")
    # TODO: Implement community detection and summary atom creation
    return "Memory consolidated"

@app.task(queue="low_priority")
def reflect_on_recent_events(user_id: str):
    """
    Reflect on recent events to update self-state.
    Triggered periodically after interactions.
    """
    print(f"Reflecting on recent events for {user_id}...")
    
    # 1. Fetch RAW history from Redis
    raw_history = context_manager.get_context(user_id)
    
    # Simple Logic: Only reflect on the last 10 messages for now
    # In production, we would use a pointer (last_reflected_index) to only process new ones
    recent_slice = raw_history[-10:] if len(raw_history) >= 10 else raw_history
    
    if not recent_slice:
        return "No events to reflect on."

    # Convert to LangChain format
    messages = []
    for msg in recent_slice:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
             messages.append(AIMessage(content=msg["content"]))

    # 2. Run Reflection Engine (LLM)
    insight = run_reflection(messages)
    
    # 3. Store Insight (if any)
    if insight:
        context_manager.save_insight(user_id, insight)
        return f"Generated Insight: {insight}"
    
    return "No significant insight found."

