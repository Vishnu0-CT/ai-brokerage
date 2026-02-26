from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import anthropic
import httpx

from app.config import settings
from app.prompts.system import build_system_prompt
from app.tools import ALL_TOOLS
from app.tools.dispatcher import ToolDispatcher
from app.utils.http_logging import EVENT_HOOKS
from app.utils.text import strip_fences

logger = logging.getLogger(__name__)

_conversation_locks: dict[str, asyncio.Lock] = {}


def _get_conversation_lock(conversation_id: str) -> asyncio.Lock:
    if conversation_id not in _conversation_locks:
        _conversation_locks[conversation_id] = asyncio.Lock()
    return _conversation_locks[conversation_id]


class ChatService:
    """Stateless chat orchestration — all persistence via BEClient."""

    def __init__(self, be_client: Any) -> None:
        from app.services.be_client import BEClient

        self.be: BEClient = be_client
        self._dispatcher = ToolDispatcher(be_client)
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url,
            http_client=httpx.AsyncClient(event_hooks=EVENT_HOOKS),
        )

    async def load_history(self, conversation_id: str) -> list[dict]:
        """Load conversation history from the BE service and reconstruct Claude message format."""
        messages = await self.be.get_messages(
            conversation_id, limit=settings.max_conversation_history,
        )

        history = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            tool_data = msg.get("tool_data")

            if role == "user":
                history.append({"role": "user", "content": content})
            elif role == "assistant":
                history.append({"role": "assistant", "content": content})
            elif role == "tool_call" and tool_data:
                history.append({
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": tool_data.get("tool_use_id", ""),
                            "name": tool_data["name"],
                            "input": tool_data["input"],
                        }
                    ],
                })
            elif role == "tool_result" and tool_data:
                history.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_data.get("tool_use_id", ""),
                            "content": content,
                        }
                    ],
                })

        return history

    async def process_message(
        self,
        conversation_id: str,
        user_message: str,
        on_tool_activity: Any = None,
    ) -> dict:
        """Process a user message and return {"voice": ..., "detail": ...}."""
        async with _get_conversation_lock(conversation_id):
            # Save user message to BE
            await self.be.save_message(conversation_id, "user", user_message)

            # Load history and build prompt concurrently
            history_coro = self.load_history(conversation_id)
            prompt_coro = build_system_prompt(self.be, conversation_id)
            history, system_prompt = await asyncio.gather(history_coro, prompt_coro)

            # Ensure current message is in history
            if not history or history[-1].get("content") != user_message:
                history.append({"role": "user", "content": user_message})

            # Tool-calling loop
            response = await self._call_claude(history, system_prompt)

            while response.stop_reason == "tool_use":
                tool_blocks = [b for b in response.content if b.type == "tool_use"]

                # Save tool calls
                for block in tool_blocks:
                    await self.be.save_message(
                        conversation_id, "tool_call", "",
                        tool_data={"tool_use_id": block.id, "name": block.name, "input": block.input},
                    )
                    if on_tool_activity:
                        on_tool_activity({"tool": block.name, "status": "calling"})

                # Execute tools
                tool_results = []
                for block in tool_blocks:
                    result = await self._dispatcher.dispatch(block.name, block.input)
                    result_str = json.dumps(result, default=str)

                    await self.be.save_message(
                        conversation_id, "tool_result", result_str,
                        tool_data={"tool_use_id": block.id},
                    )

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })

                    if on_tool_activity:
                        on_tool_activity({"tool": block.name, "status": "complete"})

                # Continue conversation
                history.append({"role": "assistant", "content": response.content})
                history.append({"role": "user", "content": tool_results})
                response = await self._call_claude(history, system_prompt)

            # Extract final text
            text_content = "".join(b.text for b in response.content if hasattr(b, "text"))
            parsed = self._parse_response(text_content)

            # Save assistant response
            await self.be.save_message(conversation_id, "assistant", text_content)

            return parsed

    async def process_message_streaming(
        self,
        conversation_id: str,
        user_message: str,
        on_voice: Any = None,
        on_detail: Any = None,
        on_tool_activity: Any = None,
    ) -> dict:
        """Process with streaming — fires on_voice as soon as voice field is extracted."""
        from app.services.pipeline import ResponseRouter

        async with _get_conversation_lock(conversation_id):
            await self.be.save_message(conversation_id, "user", user_message)

            history_coro = self.load_history(conversation_id)
            prompt_coro = build_system_prompt(self.be, conversation_id)
            history, system_prompt = await asyncio.gather(history_coro, prompt_coro)

            if not history or history[-1].get("content") != user_message:
                history.append({"role": "user", "content": user_message})

            response = None
            router = None

            while True:
                voice_captured: list[str] = []

                def _capture_voice(text: str) -> None:
                    voice_captured.append(text)

                router = ResponseRouter(on_voice=_capture_voice, on_detail=on_detail)

                async with self._client.messages.stream(
                    model=settings.anthropic_model,
                    max_tokens=4096,
                    system=system_prompt,
                    tools=ALL_TOOLS,
                    messages=history,
                ) as stream:
                    async for text in stream.text_stream:
                        router.feed(text)
                        if voice_captured and on_voice:
                            await on_voice(voice_captured[0])
                            voice_captured.clear()

                    response = await stream.get_final_message()

                if response.stop_reason != "tool_use":
                    break

                # Handle tool calls
                tool_blocks = [b for b in response.content if b.type == "tool_use"]
                for block in tool_blocks:
                    await self.be.save_message(
                        conversation_id, "tool_call", "",
                        tool_data={"tool_use_id": block.id, "name": block.name, "input": block.input},
                    )
                    if on_tool_activity:
                        on_tool_activity({"tool": block.name, "status": "calling"})

                tool_results = []
                for block in tool_blocks:
                    result = await self._dispatcher.dispatch(block.name, block.input)
                    result_str = json.dumps(result, default=str)
                    await self.be.save_message(
                        conversation_id, "tool_result", result_str,
                        tool_data={"tool_use_id": block.id},
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })
                    if on_tool_activity:
                        on_tool_activity({"tool": block.name, "status": "complete"})

                history.append({"role": "assistant", "content": response.content})
                history.append({"role": "user", "content": tool_results})

            text_content = "".join(b.text for b in response.content if hasattr(b, "text"))
            parsed = router.finalize()
            await self.be.save_message(conversation_id, "assistant", text_content)
            return parsed

    async def _call_claude(self, messages: list[dict], system_prompt: str) -> Any:
        return await self._client.messages.create(
            model=settings.anthropic_model,
            max_tokens=4096,
            system=system_prompt,
            tools=ALL_TOOLS,
            messages=messages,
        )

    def _parse_response(self, text: str) -> dict:
        """Parse the {"voice": ..., "detail": ...} format."""
        try:
            parsed = json.loads(strip_fences(text))
            if "voice" in parsed and "detail" in parsed:
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        return {"voice": text[:200], "detail": text}
