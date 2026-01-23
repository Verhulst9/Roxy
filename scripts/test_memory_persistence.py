import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from context.manager import context_manager
from tasks.interaction import process_user_input

def test_memory_persistence():
    user_id = "test_persistence_user"
    
    print(f"🧹 Clearing previous context for {user_id}...")
    context_manager.clear_context(user_id)
    
    print("\n💾 [Step 1] Injecting previous conversation into Redis (Simulating past memory)...")
    # Simulate that user previously told Nakari their favorite color
    context_manager.add_message(user_id, "user", "Remember this secret: My favorite color is Neon Green.")
    context_manager.add_message(user_id, "assistant", "Got it. I'll remember that your favorite color is Neon Green.")
    
    # Verify it's in Redis
    history = context_manager.get_context(user_id)
    print(f"   ✅ Redis now contains {len(history)} messages.")
    
    print("\n🤔 [Step 2] Testing Recall: Asking Nakari about the secret...")
    # We call the task function directly (synchronously) to test the logic flow
    # This will trigger: Redis Read -> Graph Invoke -> MiniMax Generation -> Redis Write
    response = process_user_input("What is my favorite color?", user_id)
    
    print(f"\n🤖 [Result] Nakari responded: {response}")
    
    if "green" in response.lower():
        print("\n✅ SUCCESS: Nakari remembered the context from Redis!")
    else:
        print("\n❌ FAILURE: Nakari context recall failed.")

    print("\n💾 [Step 3] Verifying new turn was persisted...")
    final_history = context_manager.get_context(user_id)
    print(f"   Redis now contains {len(final_history)} messages (Expected 2 initial + 2 new = 4).")
    
    if len(final_history) == 4:
         print("✅ Persistence cycle complete.")
    else:
         print(f"❌ Persistence mismatch. Found {len(final_history)}")

if __name__ == "__main__":
    test_memory_persistence()
