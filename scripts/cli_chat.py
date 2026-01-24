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
        print("  [SPACE] (Hold): Record Audio (Push-to-Talk)")
    print("==================================================\n")

    # Default session ID
    session_id = "cli_user_default"
    print(f"🔹 Session ID: {session_id}")

    # Audio State
    is_recording = False
    recording_data = []
    sample_rate = 16000
    
    # We'll use a queue or shared state to communicate between the keyboard callback and the main loop
    # But since input() blocks, we might need a custom input loop.
    # Actually, if we want key-based interruption, we can't use input().
    # We must implement our own "get typed input" loop using keyboard or msvcrt.
    # To keep it simple but functional for the demo: 
    # Use keyboard.read_event() loop instead of input() is too low level.
    # Compromise: We use input() for text, but 'keyboard' hooks will interrupt? 
    # No, input() captures stdin.
    
    # Better approach for CLI w/ PTT: 
    # Use a loop that checks keys periodically.
    
    current_text = ""
    
    print(f"\n[{session_id}] 👤 > ", end="", flush=True)

    while True:
        try:
            if HAS_AUDIO_DEPS:
                # Custom Event Loop for TUI-like behavior
                event = keyboard.read_event(suppress=True) # Suppress prevents echo to terminal
                
                if event.event_type == keyboard.KEY_DOWN:
                    if event.name == 'esc':
                        print("\nGoodbye! 👋")
                        break
                    
                    elif event.name == 'space':
                        if not is_recording:
                            print("\n🎤 [Recording...] (Release SPACE to finish)", end="", flush=True)
                            is_recording = True
                            recording_data = []
                            # Start recording stream
                            # sounddevice.rec is non-blocking but fixed duration. 
                            # We need InputStream for unknown duration.
                            def audio_callback(indata, frames, time, status):
                                if is_recording:
                                    recording_data.append(indata.copy())
                            
                            stream = sd.InputStream(samplerate=sample_rate, channels=1, callback=audio_callback)
                            stream.start()
                            
                    elif event.name == 'enter':
                        # Submit text input
                        if current_text:
                            user_input = current_text
                            current_text = ""
                            print() # New line
                            
                            if user_input.lower() in ["/exit", "/quit"]:
                                break
                            
                            # === CORE LOGIC ===
                            print("⏳ Nakari is thinking...")
                            response = process_user_input(user_input, session_id)
                            print(f"🤖 Nakari > {response}")
                            print(f"\n[{session_id}] 👤 > ", end="", flush=True)
                        else:
                             print(f"\n[{session_id}] 👤 > ", end="", flush=True)
                             
                    elif event.name == 'backspace':
                        if len(current_text) > 0:
                            current_text = current_text[:-1]
                            # Reprint line
                            print(f"\r[{session_id}] 👤 > {current_text} ", end="", flush=True) # space to clear chars
                            print(f"\r[{session_id}] 👤 > {current_text}", end="", flush=True)
                            
                    elif len(event.name) == 1: # Simple char
                        current_text += event.name
                        print(event.name, end="", flush=True)
                
                elif event.event_type == keyboard.KEY_UP:
                    if event.name == 'space' and is_recording:
                        is_recording = False
                        stream.stop()
                        stream.close()
                        print("\n✅ Recording finished. Processing...", flush=True)
                        
                        # Save and Transcribe
                        import numpy as np
                        if not recording_data:
                            print("❌ No audio recorded.")
                            print(f"\n[{session_id}] 👤 > {current_text}", end="", flush=True)
                            continue
                            
                        audio_np = np.concatenate(recording_data, axis=0)
                        temp_wav = "temp_voice_input.wav"
                        sf.write(temp_wav, audio_np, sample_rate)
                        
                        # Transcribe
                        try:
                            transcribed_text = transcribe_audio(temp_wav)
                            print(f"📝 You said: {transcribed_text}")
                            
                            # Send to Nakari
                            response = process_user_input(transcribed_text, session_id)
                            print(f"🤖 Nakari > {response}")
                            
                            # TTS Response
                            tts_result = synthesize_speech(response, return_bytes=True)
                            if isinstance(tts_result, dict):
                                audio_bytes = base64.b64decode(tts_result['data'])
                                play_audio_data(audio_bytes)
                            
                        except Exception as e:
                            print(f"❌ Error processing audio: {e}")
                        
                        if os.path.exists(temp_wav): os.remove(temp_wav)
                        print(f"\n[{session_id}] 👤 > {current_text}", end="", flush=True)

            else:
                # Fallback to standard input if no audio deps
                user_input = input(f"\n[{session_id}] 👤 > ").strip()
                if not user_input: continue
                if user_input.lower() in ["/exit", "/quit"]: break
                
                print("⏳ Nakari is thinking...")
                response = process_user_input(user_input, session_id)
                print(f"🤖 Nakari > {response}")

        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            break

if __name__ == "__main__":
    main()
