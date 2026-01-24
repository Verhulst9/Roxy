import asyncio
import os
import sys
import time

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio.local_provider import LocalWhisperSTT
from audio.edge_provider import EdgeTTSProvider

# Hardware I/O imports
try:
    import sounddevice as sd
    import soundfile as sf
    import pygame
except ImportError:
    print("❌ Missing hardware dependencies. Please run: pip install sounddevice soundfile pygame numpy")
    sys.exit(1)

def record_audio(filename, duration=5, samplerate=16000):
    """Record audio from microphone for a fixed duration."""
    print(f"🎤 Recording for {duration} seconds... (Please speak now)")
    try:
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
        # Display a simple countdown
        for i in range(duration, 0, -1):
            sys.stdout.write(f"\r⏳ {i}s remaining...")
            sys.stdout.flush()
            time.sleep(1)
        sd.wait()  # Wait until recording is finished
        print("\n✅ Recording finished.")
        
        # Save as WAV
        sf.write(filename, recording, samplerate)
        return True
    except Exception as e:
        print(f"❌ Recording failed: {e}")
        return False

def play_audio_data(audio_bytes):
    """Play audio bytes directly using pygame."""
    print(f"🔊 Playing {len(audio_bytes)} bytes from memory...")
    try:
        import io
        pygame.mixer.init()
        # Pygame can load from file-like object
        audio_io = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(audio_io)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        pygame.mixer.quit()
        return True
    except Exception as e:
        print(f"❌ Playback failed: {e}")
        return False

async def test_audio_pipeline():
    print("🔊 Starting Interactive Audio Module Test...")
    
    # 1. Setup Providers
    try:
        # Use a high-quality Chinese voice
        edge_tts = EdgeTTSProvider(default_voice="zh-CN-XiaoxiaoNeural")
        # Initialize STT (using 'base' for speed, 'small' or 'medium' for accuracy)
        local_stt = LocalWhisperSTT(model_size="base", device="cpu", compute_type="int8")
        print("✅ Providers initialized.")
    except Exception as e:
        print(f"❌ Failed to initialize providers. Error: {e}")
        return

    # --- Step 1: Record from Mic ---
    input_wav = "temp_mic_input.wav"
    print("\n--- [Input Phase] ---")
    if record_audio(input_wav, duration=5):
        
        # --- Step 2: Transcribe (STT) ---
        print("\n--- [Processing Phase] ---")
        try:
            print("📝 Transcribing...")
            transcribed_text = await local_stt.transcribe(input_wav)
            print(f"🗣️  You said: \"{transcribed_text}\"")
            
            # Simulated LLM Response (echoing back for now)
            reply_text = f"我听到了，你说的是：{transcribed_text}"
            
        except Exception as e:
            print(f"❌ STT failed: {e}")
            reply_text = "抱歉，我没有听清你说什么。"

        # --- Step 3: Synthesis (TTS - In Memory) ---
        print("\n--- [Output Phase] ---")
        try:
            print(f"🤖 Generating response (In-Memory): \"{reply_text}\"")
            
            # Request RAW BYTES instead of file path
            audio_bytes = await edge_tts.synthesize(reply_text, output_path=None)
            
            # --- Step 4: Playback ---
            play_audio_data(audio_bytes)
            
        except Exception as e:
            print(f"❌ TTS/Playback failed: {e}")

    # Cleanup
    print("\n🏁 Cleaning up temporary files...")
    # Only cleanup input wav, since no output file was created!
    if os.path.exists(input_wav): 
        try:
            os.remove(input_wav)
        except: 
            pass
    print("✨ Test Complete.")

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(test_audio_pipeline())
