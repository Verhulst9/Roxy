import sys
import os

# Add project root to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_core.messages import HumanMessage, SystemMessage
from llm.graph import interaction_graph

def run_chat_test():
    print("🚀 Starting Nakari Interaction Graph Test\n")
    
    # Simulate a conversation history
    # In a real app with Checkpointer, we wouldn't need to manually pass 'history' back in.
    current_messages = []
    
    # Test Data: 3 Turns
    inputs = [
        "Hello, Nakari! What is your status?",
        "I am testing your context management system.",
        "Generate a very long context to test the trimming functionality." + (" word" * 500) # Long message
    ]

    for i, user_input in enumerate(inputs):
        print(f"\n[{i+1}] 👤 User: {user_input[:100]}..." if len(user_input) > 100 else f"\n[{i+1}] 👤 User: {user_input}")
        
        # 1. Prepare State
        # We append the new HumanMessage to the existing history
        # In LangGraph with add_messages, passing the full list acts as the current state
        new_message = HumanMessage(content=user_input)
        state_input = {
            "user_id": "test_user_001",
            "messages": current_messages + [new_message],
            "response": ""
        }
        
        # 2. Invoke Graph
        # This will run: Retrieve Memory -> Manage Context -> Generate
        result = interaction_graph.invoke(state_input)
        
        # 3. Process Output
        current_messages = result["messages"] # Update history with the full state returned
        response = result["response"]
        context_window = result.get("context_window", [])
        
        print(f"[{i+1}] 🤖 Nakari: {response}")
        
        # Debug Info
        print(f"    🛠️  Debug Info:")
        print(f"    - Total History Length: {len(current_messages)} messages")
        print(f"    - Context Window Size:  {len(context_window)} messages (This is what the LLM saw)")
        
        # Check if System Prompt was preserved in Context Window (if we had one)
        # Our graph injects memory as SystemMessage in 'retrieve_long_term_memory'
        # Let's verify if the context window includes it
        system_msgs = [m for m in context_window if isinstance(m, SystemMessage)]
        print(f"    - System Prompts in Window: {len(system_msgs)}")
        if system_msgs:
            print(f"    - System Prompt Content: '{system_msgs[0].content}'")

if __name__ == "__main__":
    run_chat_test()
