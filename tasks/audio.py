from .app import app
from audio.openai_provider import OpenAITTS
from audio.local_provider import LocalWhisperSTT
from audio.edge_provider import EdgeTTSProvider
import os
import uuid

# Global instances (lazy loaded effectively by Celery worker fork usually, 
# but good to instantiate globally for connection reuse if client supports it)
# Using 'base' model on CPU by default for compatibility. Change to 'cuda'/'float16' if GPU available.
stt_provider = LocalWhisperSTT(model_size="base", device="cpu", compute_type="int8")
# Switch default TTS to EdgeTTS (Free & High Quality)
tts_provider = EdgeTTSProvider(default_voice="zh-CN-XiaoxiaoNeural")

AUDIO_TEMP_DIR = "temp_audio"
os.makedirs(AUDIO_TEMP_DIR, exist_ok=True)

@app.task(queue="interaction")
def transcribe_audio(file_path: str, language: str = None):
    """
    Celery task to transcribe audio file to text.
    """
    print(f"[STT] Transcribing audio: {file_path}")
    import asyncio
    
    # Run async function in sync Celery task
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    text = loop.run_until_complete(stt_provider.transcribe(file_path, language))
    print(f"[STT] Transcription result: {text}")
    return text

@app.task(queue="interaction")
def synthesize_speech(text: str, voice_id: str = None, return_bytes: bool = False):
    """
    Celery task to synthesize text to audio.
    If return_bytes is True, returns raw binary data (base64 encoded str usually for json serialization safety, 
    but for now we might keep it simple or stick to file path if needed).
    
    HOWEVER, Celery results are JSON serialized by default. Returning raw bytes might be tricky 
    unless using pickle serializer or encoding to base64.
    
    Safe bet: Return bytes if requested, but caller must handle decoding.
    """
    print(f"[TTS] Synthesizing speech: {text[:50]}...")
    import asyncio
    import base64
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if return_bytes:
        # No file path -> returns bytes
        audio_data = loop.run_until_complete(tts_provider.synthesize(text, voice_id, output_path=None))
        # Encode to base64 string for safe transport via Celery/Redis
        b64_audio = base64.b64encode(audio_data).decode('utf-8')
        print(f"[TTS] Audio generated ({len(audio_data)} bytes)")
        return {"data": b64_audio, "format": "mp3", "encoding": "base64"}
    else:
        # File based (Legacy/Cache friendly)
        filename = f"{uuid.uuid4()}.mp3"
        output_path = os.path.join(AUDIO_TEMP_DIR, filename)
        final_path = loop.run_until_complete(tts_provider.synthesize(text, voice_id, output_path))
        print(f"[TTS] Audio saved to: {final_path}")
        return final_path
