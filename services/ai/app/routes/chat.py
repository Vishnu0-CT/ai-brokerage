from __future__ import annotations

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.chat import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: uuid.UUID):
    await websocket.accept()
    be_client = websocket.app.state.be_client

    chat_svc = ChatService(be_client)
    conv_id = str(conversation_id)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "text")

            if msg_type == "text":
                user_message = data["content"]

                async def on_chunk(text: str) -> None:
                    await websocket.send_json({"type": "response_chunk", "content": text})

                def on_tool_activity(info):
                    asyncio.create_task(
                        websocket.send_json({"type": "tool_activity", **info})
                    )

                await chat_svc.process_message_text_streaming(
                    conv_id, user_message,
                    on_chunk=on_chunk,
                    on_tool_activity=on_tool_activity,
                )

                await websocket.send_json({"type": "response_complete"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {conversation_id}")
    except Exception:
        logger.exception(f"WebSocket error: {conversation_id}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Something went wrong. Please try again.",
            })
        except Exception:
            pass
        await websocket.close()
