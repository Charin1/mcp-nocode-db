"""
Local speech-to-text service using faster-whisper (CTranslate2).
Optimized for Apple Silicon with int8 quantization.
"""
import os
from typing import Optional
from faster_whisper import WhisperModel


class WhisperService:
    """
    A service for local speech-to-text transcription using faster-whisper.
    Uses int8 quantization for efficient inference on Apple Silicon.
    """

    _instance: Optional["WhisperService"] = None
    _model: Optional[WhisperModel] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_model(self) -> WhisperModel:
        """
        Lazily initializes and returns the Whisper model.
        Model is downloaded on first use.
        """
        if self._model is None:
            model_size = os.getenv("WHISPER_MODEL", "distil-medium.en")
            # CTranslate2 is highly optimized for ARM CPUs (Apple Silicon)
            # int8 provides a good balance of speed and memory efficiency
            self._model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8"
            )
            print(f"Whisper model '{model_size}' loaded with int8 quantization.")
        return self._model

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"  # or "translate" to translate to English
    ) -> dict:
        """
        Transcribes an audio file to text.

        Args:
            audio_path: Path to the audio file (supports mp3, wav, m4a, etc.).
            language: Optional language code (e.g., "en", "es"). Auto-detected if None.
            task: "transcribe" for same-language, "translate" for English translation.

        Returns:
            dict with "text" (full transcription) and "segments" (with timestamps).
        """
        model = self._get_model()

        # First try with VAD enabled but with relaxed parameters
        segments, info = model.transcribe(
            audio_path,
            language=language,
            task=task,
            beam_size=5,
            vad_filter=True,
            vad_parameters={
                "threshold": 0.3,  # Lower threshold = more sensitive to speech (default 0.5)
                "min_speech_duration_ms": 100,  # Shorter minimum speech duration (default 250)
                "min_silence_duration_ms": 300,  # More tolerance for pauses (default 2000)
            }
        )

        # Collect all segments
        all_segments = []
        full_text_parts = []
        for segment in segments:
            all_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            full_text_parts.append(segment.text.strip())

        # If VAD filtered out everything, try again without VAD
        if not full_text_parts and info.duration > 0.5:
            print("VAD filtered all audio, retrying without VAD...")
            segments_no_vad, info = model.transcribe(
                audio_path,
                language=language,
                task=task,
                beam_size=5,
                vad_filter=False
            )
            for segment in segments_no_vad:
                all_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
                full_text_parts.append(segment.text.strip())

        return {
            "text": " ".join(full_text_parts),
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "segments": all_segments
        }


# Singleton accessor
def get_whisper_service() -> WhisperService:
    return WhisperService()
