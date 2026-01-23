from .app import app
from llm.graph import interaction_graph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from context import context_manager # We still use this for persistence for now

@app.task(queue="high_priority")
def process_user_input(user_input: str, user_id: str):
    """
    Handle user input (Text/Audio/Vision).
    Uses LangGraph to orchestrate the interaction flow and connects to Persistent Context.
    """
    print(f"Processing user input from {user_id}: {user_input}")
    
    # 1. Retrieve Historical Context from Redis
    raw_history = context_manager.get_context(user_id)
    print(f"Loaded {len(raw_history)} messages from history.")
    
    # 2. Convert raw JSON history to LangChain Message Objects
    langchain_messages = []
    for msg in raw_history:
        role = msg.get("role")
        content = msg.get("content")
        if role == "user":
            langchain_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            langchain_messages.append(AIMessage(content=content))
        # Note: We skip system messages here if we want them to be managed freshly by the graph,
        # or we can include them if they were persisted.
    
    # 3. Add current user input to the list
    # LangGraph will process this full list (History + New Input),
    # and the 'manage_context' node inside the graph will handle the actual Token Trimming.
    
    # Important: In LangGraph 'add_messages' reducer mode, we usually pass NEW messages.
    # But since we are stateless between tasks (no checkpointer yet), we pass FULL history.
    # The 'checkpointer' optimization would allow us to only pass the new message.
    current_messages = langchain_messages + [HumanMessage(content=user_input)]

    initial_state = {
        "user_id": user_id, 
        "messages": current_messages, # Seed with Full History
        "response": ""
    }
    
    # 4. Execute Graph (Think)
    result = interaction_graph.invoke(initial_state)
    
    response_text = result["response"]
    print(f"Final Response: {response_text}")
    
    # 5. Persist the New Turn (Write Back)
    # We only need to append the new user input and the new response.
    # The older history is already in Redis.
    context_manager.add_message(user_id, "user", user_input)
    context_manager.add_message(user_id, "assistant", response_text)
    
    # 6. Trigger Reflection (Fire & Forget)
    # New Logic: Event-Driven Trigger based on LLM Signal
    should_reflect = result.get("should_reflect", False)
    
    if should_reflect:
        print(f"✨ LLM decided to trigger Background Reflection for {user_id}...")
        from tasks.reflection import reflect_on_recent_events
        reflect_on_recent_events.apply_async(args=(user_id,), queue="low_priority")
    else:
        print("💤 No reflection needed for this turn.")

    return response_text

@app.task(queue="high_priority")
def generate_voice(text: str):
    """
    TTS generation task.
    """
    print(f"Generating voice for: {text}")
    # TODO: Call TTS service
    return "audio_data_placeholder"
