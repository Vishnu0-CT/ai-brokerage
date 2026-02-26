from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.be_client import BEClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI service...")

    # 1. Initialize BE client
    be_client = BEClient(
        base_url=settings.be_service_url,
        timeout=settings.be_service_timeout,
    )

    # 2. Verify BE service is reachable
    try:
        await be_client.health()
        logger.info(f"BE service reachable at {settings.be_service_url}")
    except Exception:
        logger.warning(
            f"BE service not reachable at {settings.be_service_url} — "
            "will retry on first request"
        )

    app.state.be_client = be_client

    # 3. Preload Kokoro TTS model
    try:
        from kokoro_onnx import Kokoro
        from pipecat.services.kokoro.tts import KOKORO_CACHE_DIR, _ensure_model_files

        model_path = KOKORO_CACHE_DIR / "kokoro-v1.0.onnx"
        voices_path = KOKORO_CACHE_DIR / "voices-v1.0.bin"
        _ensure_model_files(model_path, voices_path)
        app.state.kokoro = Kokoro(str(model_path), str(voices_path))
        logger.info(f"Kokoro TTS loaded ({len(app.state.kokoro.get_voices())} voices)")
    except Exception:
        logger.warning("Kokoro TTS not available — /api/tts will return 503", exc_info=True)
        app.state.kokoro = None

    # 4. Preload Whisper STT model
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(settings.whisper_model)
        logger.info(f"Whisper model ready: {settings.whisper_model}")
    except Exception:
        logger.warning("Whisper model preload failed — will download on first voice request", exc_info=True)

    logger.info("AI service startup complete")

    yield

    # Shutdown
    logger.info("Shutting down AI service...")
    await be_client.close()
    logger.info("AI service shutdown complete")


app = FastAPI(title="AI Brokerage — AI Service", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.routes.health import router as health_router
from app.routes.chat import router as chat_router
from app.routes.tts import router as tts_router

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(tts_router)

# Voice route — registered but requires pipecat to function
try:
    from app.routes.voice import router as voice_router
    app.include_router(voice_router)
except ImportError:
    logger.info("Voice route not available — pipecat not installed")
