import sys
import os
from langchain_core.messages import HumanMessage, SystemMessage

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from context.manager import context_manager
from llm.graph import interaction_graph

def test_insight_injection():
    user_id = "test_insight_user"
    test_insight = "User is a secret agent designated 007."
    
    print(f"🧹 Clearing context for {user_id}...")
    context_manager.clear_context(user_id)
    # Also clear insights (needs direct redis access or we just assume save_insight pushes to a key we can expire/delete)
    # ContextManager doesn't have a clear_insights method yet, let's just use a fresh user or overwrite via redis directly if needed.
    # Since we push to a list, old insights might remain. Let's rely on clear_context clearing the main context, 
    # but for insights, let's manually delete the key to be sure.
    context_manager.redis.delete(f"nakari:insights:{user_id}")

    print(f"\n💉 [Step 1] Manually injecting a fake insight:")
    print(f"   Insight: '{test_insight}'")
    context_manager.save_insight(user_id, test_insight)

    print("\n🏃 [Step 2] Running Interaction Graph...")
    input_text = "Who am I?"
    initial_state = {
        "user_id": user_id, 
        "messages": [HumanMessage(content=input_text)],
        "response": ""
    }
    
    # We invoke the graph directly to inspect the internal state flow
    result = interaction_graph.invoke(initial_state)
    
    print("\n🔍 [Step 3] Inspecting Context Window sent to LLM...")
    context_window = result.get("context_window", [])
    
    found_insight = False
    for msg in context_window:
        if isinstance(msg, SystemMessage):
            print(f"   Found SystemMessage: {msg.content}")
            if test_insight in msg.content:
                found_insight = True
                print("   ✅ MATCH: The injected insight was found in the System Message.")
    
    if not found_insight:
        print("   ❌ FAILURE: The insight was NOT found in the context window.")
    
    print(f"\n🤖 [Step 4] Checking Model Response...")
    print(f"   Response: {result['response']}")
    
    if "007" in result['response'] or "secret agent" in result['response'].lower():
        print("   ✅ SUCCESS: The model used the insight to answer.")
    else:
        print("   ⚠️ WARNING: Model might not have used the insight or answered vaguely.")

if __name__ == "__main__":
    test_insight_injection()
