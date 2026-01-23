import sys
import os
import uuid

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tasks.interaction import process_user_input
from context.manager import context_manager

def main():
    print("==================================================")
    print("          Nakari CLI Interaction Terminal         ")
    print("==================================================")
    print("Commands:")
    print("  /exit, /quit : Exit the chat")
    print("  /clear       : Clear conversation memory")
    print("  /new         : Start a new session ID")
    print("==================================================\n")

    # Default session ID
    session_id = "cli_user_default"
    print(f"🔹 Session ID: {session_id}")

    while True:
        try:
            user_input = input(f"\n[{session_id}] 👤 > ").strip()
            
            if not user_input:
                continue

            if user_input.lower() in ["/exit", "/quit"]:
                print("Goodbye! 👋")
                break
            
            if user_input.lower() == "/clear":
                context_manager.clear_context(session_id)
                print(f"🧹 Context cleared for {session_id}.")
                continue

            if user_input.lower() == "/new":
                session_id = f"user_{str(uuid.uuid4())[:8]}"
                print(f"🆕 Switched to new Session ID: {session_id}")
                continue

            # Process input using the core Nakari logic
            # Calling the task function directly executes it locally (synchronously) for testing
            # effectively mocking the Worker execution in this process.
            print("⏳ Nakari is thinking...")
            response = process_user_input(user_input, session_id)
            
            # The output is already printed by process_user_input, but let's print it cleanly here too if needed
            # process_user_input currently prints "Final Response: ..."
            # We can format it nicely here.
            print(f"🤖 Nakari > {response}")

        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
