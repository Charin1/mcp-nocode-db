"""
API router for audio transcription using local Whisper.
"""
import os
import tempfile
import shutil
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from services.whisper_service import get_whisper_service


router = APIRouter(prefix="/api/transcribe", tags=["Transcription"])


class TranscriptionResponse(BaseModel):
    text: str
    language: str
    language_probability: float
    duration: float
    segments: list


@router.post("", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    task: str = Form("transcribe")
):
    """
    Transcribe an audio file to text using local Whisper model.

    - **file**: Audio file (mp3, wav, m4a, etc.)
    - **language**: Optional language code (auto-detected if not provided)
    - **task**: "transcribe" (same language) or "translate" (to English)
    """
    # Validate file type
    allowed_extensions = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save uploaded file to a temp location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Perform transcription
        whisper_service = get_whisper_service()
        result = whisper_service.transcribe(
            audio_path=tmp_path,
            language=language,
            task=task
        )

        return TranscriptionResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    finally:
        # Cleanup temp file
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
