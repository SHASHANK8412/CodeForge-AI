"""
Voice input: speech to text on this machine (backend/ml/local_models.py, faster-whisper).

POST /api/speech/transcribe takes one short recording (the browser's MediaRecorder output, webm/ogg/wav/mp3/m4a) and
returns its text. The audio is written to a private temporary file, transcribed locally and deleted; it is never sent to
another service or stored. Signed-in users only; size and length are bounded.
"""

import asyncio
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/speech", tags=["speech"])

MAX_BYTES = 10 * 1024 * 1024          # about 10 minutes of browser opus audio; requests are prompts, not dictation
MAX_SECONDS = 180
_SUFFIXES = {"audio/webm": ".webm", "audio/ogg": ".ogg", "audio/wav": ".wav", "audio/x-wav": ".wav",
             "audio/mpeg": ".mp3", "audio/mp4": ".m4a", "audio/x-m4a": ".m4a"}


@router.get("/status")
def speech_status(user: dict = Depends(get_current_user)):
    """Whether voice input is available (the model is configured); it loads on the first recording."""
    from backend.ml.local_models import status as model_status
    s = model_status()["speech"]
    return {"available": s["state"] != "off" and s["state"] != "unavailable", **s}


@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), language: Optional[str] = Form(None),
                     user: dict = Depends(get_current_user)):
    content_type = (audio.content_type or "").split(";")[0].strip().lower()
    if content_type not in _SUFFIXES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"unsupported audio type: {content_type or 'none'}")
    data = await audio.read(MAX_BYTES + 1)
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "the recording is empty")
    if len(data) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "the recording is too long")
    if language is not None and not (language.isalpha() and 2 <= len(language) <= 3):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "language must be a 2-3 letter code, e.g. en")

    from backend.ml import local_models
    fd, path = tempfile.mkstemp(prefix="aiforge_voice_", suffix=_SUFFIXES[content_type])
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        try:
            # CPU work: off the event loop so live build progress keeps streaming
            result = await asyncio.to_thread(local_models.transcribe, path, language)
        except Exception as e:  # noqa: BLE001 - an undecodable file is the client's problem, reported plainly
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"could not decode the recording ({type(e).__name__})")
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    if result is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "voice input is unavailable: the speech model is switched off or not downloaded "
                            "(python -m backend.ml.local_models download speech)")
    if result["duration_seconds"] > MAX_SECONDS:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"recordings are limited to {MAX_SECONDS} s")
    return result
