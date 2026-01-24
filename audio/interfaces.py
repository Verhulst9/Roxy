from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Union
import os

class STTProvider(ABC):
    """
    Abstract Base Class for Speech-to-Text (STT) providers.
    """
    
    @abstractmethod
    async def transcribe(self, audio_file: Union[str, BinaryIO], language: Optional[str] = None) -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio_file: Path to audio file or file-like object (bytes).
            language: ISO 639-1 language code (e.g., 'en', 'zh'). If None, auto-detect.
            
        Returns:
            The transcribed text string.
        """
        pass

class TTSProvider(ABC):
    """
    Abstract Base Class for Text-to-Speech (TTS) providers.
    """
    
    @abstractmethod
    async def synthesize(self, text: str, voice_id: Optional[str] = None, output_path: Optional[str] = None) -> Union[str, bytes]:
        """
        Synthesize text to audio.
        
        Args:
            text: The text content to speak.
            voice_id: Identifier for the specific voice/timbre.
            output_path: Optional path to save the file. If None, return raw bytes.
            
        Returns:
            Path to the generated audio file (str) or raw audio bytes (bytes).
        """
        pass
    
    @abstractmethod
    async def get_available_voices(self) -> list[dict]:
        """
        Return a list of available voices.
        """
        pass
