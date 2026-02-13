import os
from typing import Optional, Union, BinaryIO
from .interfaces import STTProvider

class LocalWhisperSTT(STTProvider):
    """
    Local STT provider using faster-whisper.
    """
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        """
        Initialize the Local Whisper model.
        
        Args:
            model_size: Model size ('tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3').
            device: 'cuda' for GPU or 'cpu'.
            compute_type: 'float16' for GPU, 'int8' for CPU.
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError("Please install faster-whisper: pip install faster-whisper")

        print(f"[Whisper] Loading Model ({model_size}) on {device}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("[Whisper] Model loaded.")

    async def transcribe(self, audio_file: Union[str, BinaryIO], language: Optional[str] = None) -> str:
        # faster-whisper primarily accepts file paths or file-like objects (binary)
        # Note: faster-whisper is synchronous/blocking. We wrap it in a blocking call if needed,
        # but since this is called from a Celery task (which is sync), we can run it directly.
        # However, to conform to the async interface, we just run it and return.
        
        # If input is bytes/file-like, ensure it's at the start or handled correctly.
        # faster-whisper `transcribe` supports file-like objects.
        
        segments, info = self.model.transcribe(audio_file, language=language)
        
        # Collect all segments
        text_segments = [segment.text for segment in segments]
        full_text = "".join(text_segments).strip()
        
        return full_text
