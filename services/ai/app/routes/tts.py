from __future__ import annotations

import io
import struct

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter(prefix="/api/tts", tags=["tts"])

DEFAULT_VOICE = "af_heart"


class TTSRequest(BaseModel):
    text: str
    voice: str = DEFAULT_VOICE
    speed: float = 1.0


def _numpy_to_wav(samples, sample_rate: int) -> bytes:
    """Convert float32 numpy array to WAV bytes (16-bit PCM)."""
    import numpy as np

    pcm = (samples * 32767).clip(-32768, 32767).astype(np.int16)
    raw = pcm.tobytes()

    buf = io.BytesIO()
    num_channels = 1
    sample_width = 2  # 16-bit
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + len(raw)))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))
    buf.write(struct.pack("<H", 1))  # PCM format
    buf.write(struct.pack("<H", num_channels))
    buf.write(struct.pack("<I", sample_rate))
    buf.write(struct.pack("<I", sample_rate * num_channels * sample_width))
    buf.write(struct.pack("<H", num_channels * sample_width))
    buf.write(struct.pack("<H", sample_width * 8))
    buf.write(b"data")
    buf.write(struct.pack("<I", len(raw)))
    buf.write(raw)

    return buf.getvalue()


@router.post("")
async def synthesize(body: TTSRequest, request: Request):
    kokoro = request.app.state.kokoro
    if kokoro is None:
        raise HTTPException(status_code=503, detail="TTS model not loaded")

    samples, sr = kokoro.create(body.text, voice=body.voice, speed=body.speed, lang="en-us")
    wav_bytes = _numpy_to_wav(samples, sr)

    return Response(content=wav_bytes, media_type="audio/wav")


@router.get("/voices")
async def list_voices(request: Request):
    kokoro = request.app.state.kokoro
    if kokoro is None:
        raise HTTPException(status_code=503, detail="TTS model not loaded")

    return {"voices": kokoro.get_voices()}
