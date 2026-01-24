import os
import asyncio
from typing import Optional, Union
from .interfaces import TTSProvider

class EdgeTTSProvider(TTSProvider):
    """
    TTS provider using Microsoft Edge's online text-to-speech service (via edge-tts).
    Free, high quality, low latency.
    """
    def __init__(self, default_voice: str = "zh-CN-XiaoxiaoNeural"):
        """
        Args:
            default_voice: The voice ID to use by default. 
                           Examples: 'zh-CN-XiaoxiaoNeural', 'en-US-AriaNeural'.
        """
        try:
            import edge_tts
        except ImportError:
            raise ImportError("Please install edge-tts: pip install edge-tts")
        
        self.default_voice = default_voice

    async def synthesize(self, text: str, voice_id: Optional[str] = None, output_path: Optional[str] = None) -> Union[str, bytes]:
        """
        Synthesize text to audio. If output_path is None, returns raw bytes (mp3 format).
        """
        import edge_tts
        
        voice = voice_id or self.default_voice
        communicate = edge_tts.Communicate(text, voice)
        
        if output_path:
            await communicate.save(output_path)
            return output_path
        else:
            # Memory-only stream
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            return audio_data

    async def get_available_voices(self) -> list[dict]:
        import edge_tts
        voices = await edge_tts.list_voices()
        # Convert to our standardized dict format
        return [
            {
                "id": v["ShortName"], 
                "name": v["FriendlyName"], 
                "gender": v["Gender"],
                "locale": v["Locale"]
            }
            for v in voices
        ]
