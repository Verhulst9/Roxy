import sys
import os
import uuid
import time
import base64
import io
import asyncio
import threading

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tasks.interaction import process_user_input
from tasks.audio import transcribe_audio, synthesize_speech
from context.manager import context_manager

# Conditional imports for Audio/Keyboard
try:
    import keyboard
    import sounddevice as sd
    import soundfile as sf
    import pygame
    HAS_AUDIO_DEPS = True
except ImportError:
    HAS_AUDIO_DEPS = False
    print("⚠️  Audio/Input dependencies missing. Run: pip install keyboard sounddevice soundfile pygame")

def play_audio_data(audio_bytes):
    """Play audio bytes using pygame."""
    if not HAS_AUDIO_DEPS: return
    try:
        pygame.mixer.init()
        audio_io = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(audio_io)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        pygame.mixer.quit()
    except Exception as e:
        print(f"❌ Playback failed: {e}")

def main():
    print("==================================================")
    print("          Nakari CLI Interaction Terminal         ")
    print("==================================================")
    print("Commands:")
    print("  /exit, /quit : Exit the chat")
    print("  /clear       : Clear conversation memory")
    print("  /new         : Start a new session ID")
    if HAS_AUDIO_DEPS:
        print("  [F5] (Hold): Record Audio (Push-to-Talk)")
    print("==================================================\n")

    # Default session ID
    session_id = "cli_user_default"
    print(f"🔹 Session ID: {session_id}")

    # Audio State
    audio_state = {
        "is_recording": False,
        "recording_data": [],
        "stream": None,
        "sample_rate": 16000 # Store sample rate in state
    }
    
    # --- Background F5 Listener Logic ---
    def f5_monitor_thread():
        if not HAS_AUDIO_DEPS: return
        
        was_pressed = False
        sample_rate = audio_state["sample_rate"] # Local ref
        
        while True:
            # Check F5 state without suppressing other keys
            try:
                is_pressed = keyboard.is_pressed('f5')
            except:
                is_pressed = False
                
            if is_pressed and not was_pressed:
                # === F5 DOWN (Start) ===
                was_pressed = True
                audio_state["is_recording"] = True
                audio_state["recording_data"] = []
                print("\n🎤 [Recording...] (Release F5 to finish)", end="", flush=True)
                
                def audio_callback(indata, frames, time, status):
                    if audio_state["is_recording"]:
                        audio_state["recording_data"].append(indata.copy())
                
                # Start stream
                try:
                    audio_state["stream"] = sd.InputStream(samplerate=sample_rate, channels=1, callback=audio_callback)
                    audio_state["stream"].start()
                except Exception as e:
                    print(f"❌ Audio Error: {e}")

            elif not is_pressed and was_pressed:
                # === F5 UP (Stop & Process) ===
                was_pressed = False
                audio_state["is_recording"] = False
                if audio_state["stream"]:
                    audio_state["stream"].stop()
                    audio_state["stream"].close()
                
                print("\n✅ Processing Voice...", flush=True)
                
                # Background processing (so we don't block the F5 loop, though this loop is already a thread)
                # But we want to print to stdout which might collide with input()
                
                import numpy as np
                if not audio_state["recording_data"]:
                    continue
                    
                try:
                    audio_np = np.concatenate(audio_state["recording_data"], axis=0)
                    temp_wav = f"temp_voice_{str(uuid.uuid4())[:8]}.wav"
                    sf.write(temp_wav, audio_np, sample_rate)
                    
                    # STT
                    print(f"📝 Transcribing...", flush=True)
                    transcribed_text = transcribe_audio(temp_wav)
                    print(f"\n🗣️ You (Voice): {transcribed_text}")
                    
                    if os.path.exists(temp_wav): os.remove(temp_wav)
                    
                    if transcribed_text.strip():
                        # Core Logic
                        print("⏳ Nakari is thinking...", flush=True)
                        response = process_user_input(transcribed_text, session_id)
                        print(f"🤖 Nakari > {response}")
                        print(f"[{session_id}] 👤 > ", end="", flush=True) # Restore prompt visual
                        
                        # TTS
                        tts_result = synthesize_speech(response, return_bytes=True)
                        if isinstance(tts_result, dict):
                            audio_bytes = base64.b64decode(tts_result['data'])
                            play_audio_data(audio_bytes)
                            
                except Exception as e:
                    print(f"❌ Voice Process Error: {e}")

            time.sleep(0.05) # Poll rate

    # Start listener in background thread
    if HAS_AUDIO_DEPS:
        listener = threading.Thread(target=f5_monitor_thread, daemon=True)
        listener.start()

    # --- Main Text Input Loop ---
    # Using standard input() allows Ctrl+C and IME to work normally
    
    print(f"\n[{session_id}] 👤 > ", end="", flush=True)
    
    while True:
        try:
            # Standard blocking input
            # Note: If voice output prints while this is blocking, the prompt line might look messy
            # but functionality is preserved.
            user_input = input().strip()
            
            if not user_input:
                print(f"[{session_id}] 👤 > ", end="", flush=True)
                continue

            if user_input.lower() in ["/exit", "/quit"]:
                print("Goodbye! 👋")
                break
            
            if user_input.lower() == "/clear":
                context_manager.clear_context(session_id)
                print(f"🧹 Context cleared for {session_id}.")
                print(f"[{session_id}] 👤 > ", end="", flush=True)
                continue

            if user_input.lower() == "/new":
                session_id = f"user_{str(uuid.uuid4())[:8]}"
                print(f"🆕 Switched to new Session ID: {session_id}")
                print(f"[{session_id}] 👤 > ", end="", flush=True)
                continue

            # Text Processing
            print("⏳ Nakari is thinking...")
            response = process_user_input(user_input, session_id)
            print(f"🤖 Nakari > {response}")
            print(f"[{session_id}] 👤 > ", end="", flush=True)

        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            # Keep running loop on error


if __name__ == "__main__":
    main()
