import sys
import os
import redis
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from context.manager import context_manager

def debug_insights():
    # 1. Inspect Redis directly
    session_id = "cli_user_default"
    key = f"nakari:insights:{session_id}"
    
    print(f"🔍 Inspecting Redis Key: {key}")
    
    if not context_manager.redis.exists(key):
        print(f"❌ Key {key} does not exist in Redis.")
    else:
        type_ = context_manager.redis.type(key)
        print(f"✅ Key exists. Type: {type_}")
        
        len_ = context_manager.redis.llen(key)
        print(f"📊 List Length: {len_}")
        
        items = context_manager.redis.lrange(key, 0, -1)
        print(f"📋 Items in Redis:")
        for i, item in enumerate(items):
            print(f"   [{i}] {item}")

    # 2. Test Manager Method
    print(f"\n🧪 Testing context_manager.get_insights('{session_id}')...")
    insights = context_manager.get_insights(session_id)
    print(f"   Result: {insights}")
    
    if not insights:
        print("   ⚠️ get_insights returned empty list, even if Redis has data (check logic?)")

if __name__ == "__main__":
    debug_insights()
