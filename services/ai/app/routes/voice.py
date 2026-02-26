from __future__ import annotations

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, WebSocket

from app.services.chat import ChatService
from app.services.pipeline import (
    create_chat_processor,
    create_stt,
    create_tts,
    create_transport,
    run_voice_pipeline,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice"])


@router.websocket("/ws/voice/{conversation_id}")
async def websocket_voice(websocket: WebSocket, conversation_id: uuid.UUID):
    """Full voice pipeline: mic audio → STT → ChatService → TTS → audio out."""
    await websocket.accept()
    be_client = websocket.app.state.be_client

    chat_svc = ChatService(be_client)
    conv_id = str(conversation_id)

    transport = create_transport(websocket)
    stt = create_stt()
    tts = create_tts()

    def on_detail(detail_text: str):
        async def _send():
            try:
                await websocket.send_text(
                    json.dumps({"type": "detail", "content": detail_text})
                )
            except Exception:
                pass

        asyncio.create_task(_send())

    chat_processor = create_chat_processor(
        chat_service=chat_svc,
        conversation_id=conv_id,
        on_detail=on_detail,
    )

    logger.info(f"Voice pipeline starting: {conversation_id}")
    try:
        await run_voice_pipeline(transport, stt, tts, chat_processor)
    except Exception:
        logger.exception(f"Voice pipeline error: {conversation_id}")
    finally:
        logger.info(f"Voice pipeline ended: {conversation_id}")
