import os
from typing import Optional, Union, BinaryIO
from .interfaces import STTProvider, TTSProvider
from openai import AsyncOpenAI

class OpenAIWhisperSTT(STTProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    async def transcribe(self, audio_file: Union[str, BinaryIO], language: Optional[str] = None) -> str:
        # If it's a path, open it. 
        # OpenAI API expects a file-like object with a name attribute usually, 
        # or we just pass the path if using the client helper?
        # The async client follows standard params.
        
        should_close = False
        if isinstance(audio_file, str):
            file_obj = open(audio_file, "rb")
            should_close = True
        else:
            file_obj = audio_file

        try:
            transcription = await self.client.audio.transcriptions.create(
                model="whisper-1", 
                file=file_obj,
                language=language
            )
            return transcription.text
        finally:
            if should_close:
                file_obj.close()


class OpenAITTS(TTSProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.default_voice = "alloy"

    async def synthesize(self, text: str, voice_id: Optional[str] = None, output_path: Optional[str] = None) -> Union[str, bytes]:
        voice = voice_id or self.default_voice
        
        response = await self.client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # If path provided, save to file
        if output_path:
            response.stream_to_file(output_path)
            return output_path
        
        # Else return raw bytes
        return response.content

    async def get_available_voices(self) -> list[dict]:
        return [
            {"id": "alloy", "name": "Alloy", "gender": "neutral"},
            {"id": "echo", "name": "Echo", "gender": "male"},
            {"id": "fable", "name": "Fable", "gender": "neutral"},
            {"id": "onyx", "name": "Onyx", "gender": "male"},
            {"id": "nova", "name": "Nova", "gender": "female"},
            {"id": "shimmer", "name": "Shimmer", "gender": "female"},
        ]
