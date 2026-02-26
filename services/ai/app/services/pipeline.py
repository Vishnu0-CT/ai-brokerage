from __future__ import annotations

import asyncio
import json
import logging
import math
import struct
from typing import Any

logger = logging.getLogger(__name__)

# ── Acknowledgment chime (generated once at import time) ────────────
_CHIME_SR = 24000


def _generate_chime() -> bytes:
    """Short two-tone acknowledgment chime as PCM int16 LE."""
    duration = 0.12  # 120 ms
    n = int(_CHIME_SR * duration)
    f1, f2 = 523.25, 659.25  # C5 + E5 (major third)
    data = []
    for i in range(n):
        t = i / _CHIME_SR
        env = math.exp(-t * 20)  # fast exponential decay
        sample = 0.25 * env * (
            0.6 * math.sin(2 * math.pi * f1 * t)
            + 0.4 * math.sin(2 * math.pi * f2 * t)
        )
        data.append(max(-32768, min(32767, int(sample * 32767))))
    return struct.pack(f"<{n}h", *data)


ACK_CHIME = _generate_chime()


class ResponseRouter:
    """
    Parses the dual {"voice": ..., "detail": ...} response from Claude.
    Extracts voice field early for TTS, sends detail to WebSocket.
    """

    def __init__(self, on_voice: Any = None, on_detail: Any = None) -> None:
        self._on_voice = on_voice
        self._on_detail = on_detail
        self._buffer = ""

    def feed(self, chunk: str) -> None:
        self._buffer += chunk

        # Try to extract voice field early for low-latency TTS
        if self._on_voice and '"voice"' in self._buffer:
            try:
                voice_start = self._buffer.index('"voice"') + len('"voice"')
                colon_pos = self._buffer.index(":", voice_start)
                quote_start = self._buffer.index('"', colon_pos + 1)
                pos = quote_start + 1
                while pos < len(self._buffer):
                    if self._buffer[pos] == '"' and self._buffer[pos - 1] != '\\':
                        voice_text = self._buffer[quote_start + 1:pos]
                        self._on_voice(voice_text)
                        self._on_voice = None  # Only emit once
                        break
                    pos += 1
            except (ValueError, IndexError):
                pass  # Not enough data yet

    def finalize(self) -> dict:
        """Called when streaming is complete. Returns parsed response."""
        from app.utils.text import strip_fences

        try:
            parsed = json.loads(strip_fences(self._buffer))
            if self._on_detail:
                self._on_detail(parsed.get("detail", ""))
            return parsed
        except json.JSONDecodeError:
            result = {"voice": self._buffer[:200], "detail": self._buffer}
            if self._on_detail:
                self._on_detail(self._buffer)
            return result


# ── Pipecat integration (imported lazily to avoid hard dependency) ──

def _import_pipecat():
    """Lazily import pipecat modules. Raises ImportError if not installed."""
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.audio.vad.vad_analyzer import VADParams
    from pipecat.frames.frames import (
        Frame,
        LLMFullResponseEndFrame,
        LLMFullResponseStartFrame,
        OutputAudioRawFrame,
        TextFrame,
        TranscriptionFrame,
    )
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
    from pipecat.serializers.protobuf import ProtobufFrameSerializer
    from pipecat.services.whisper.stt import WhisperSTTServiceMLX, MLXModel, Language
    from pipecat.services.kokoro.tts import KokoroTTSService
    from pipecat.transports.websocket.fastapi import (
        FastAPIWebsocketParams,
        FastAPIWebsocketTransport,
    )
    return {
        "SileroVADAnalyzer": SileroVADAnalyzer,
        "VADParams": VADParams,
        "Frame": Frame,
        "LLMFullResponseEndFrame": LLMFullResponseEndFrame,
        "LLMFullResponseStartFrame": LLMFullResponseStartFrame,
        "OutputAudioRawFrame": OutputAudioRawFrame,
        "TextFrame": TextFrame,
        "TranscriptionFrame": TranscriptionFrame,
        "Pipeline": Pipeline,
        "PipelineRunner": PipelineRunner,
        "PipelineParams": PipelineParams,
        "PipelineTask": PipelineTask,
        "FrameDirection": FrameDirection,
        "FrameProcessor": FrameProcessor,
        "ProtobufFrameSerializer": ProtobufFrameSerializer,
        "WhisperSTTServiceMLX": WhisperSTTServiceMLX,
        "MLXModel": MLXModel,
        "Language": Language,
        "KokoroTTSService": KokoroTTSService,
        "FastAPIWebsocketParams": FastAPIWebsocketParams,
        "FastAPIWebsocketTransport": FastAPIWebsocketTransport,
    }


def create_chat_processor(
    chat_service: Any,
    conversation_id: str,
    on_detail: Any = None,
    **kwargs,
):
    """Factory that creates a ChatProcessor with FrameProcessor as its base class.

    Pipecat's Pipeline checks isinstance(processor, FrameProcessor). A plain class
    that manually calls FrameProcessor.__init__ on self will fail that check.
    This factory builds the class at runtime so the inheritance is real.
    """
    pc = _import_pipecat()
    FrameProcessor = pc["FrameProcessor"]

    class ChatProcessor(FrameProcessor):
        def __init__(self):
            super().__init__(name="ChatProcessor", **kwargs)
            self._chat_service = chat_service
            self._conversation_id = conversation_id
            self._on_detail = on_detail
            self._pc = pc

        async def process_frame(self, frame, direction):
            pc = self._pc
            await super().process_frame(frame, direction)

            if isinstance(frame, pc["TranscriptionFrame"]) and frame.text.strip():
                logger.info(f"Transcription: {frame.text!r}")
                voice_pushed = False
                try:
                    # Immediate audio acknowledgment
                    await self.push_frame(pc["OutputAudioRawFrame"](
                        audio=ACK_CHIME, sample_rate=_CHIME_SR, num_channels=1,
                    ))

                    voice_event = asyncio.Event()
                    voice_holder: list[str] = []

                    async def _on_voice(text: str) -> None:
                        voice_holder.append(text)
                        voice_event.set()

                    streaming_task = asyncio.create_task(
                        self._chat_service.process_message_streaming(
                            self._conversation_id,
                            frame.text,
                            on_voice=_on_voice,
                            on_detail=self._on_detail,
                        )
                    )

                    event_waiter = asyncio.create_task(voice_event.wait())
                    await asyncio.wait(
                        {event_waiter, streaming_task},
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    if voice_holder:
                        await self.push_frame(pc["LLMFullResponseStartFrame"]())
                        await self.push_frame(pc["TextFrame"](text=voice_holder[0]))
                        await self.push_frame(pc["LLMFullResponseEndFrame"]())
                        voice_pushed = True

                    result = await streaming_task

                    if voice_pushed and len(voice_holder) > 1 and voice_holder[-1] != voice_holder[0]:
                        await self.push_frame(pc["LLMFullResponseStartFrame"]())
                        await self.push_frame(pc["TextFrame"](text=voice_holder[-1]))
                        await self.push_frame(pc["LLMFullResponseEndFrame"]())

                    if not voice_pushed:
                        voice_text = result.get("voice", "")
                        if voice_text:
                            await self.push_frame(pc["LLMFullResponseStartFrame"]())
                            await self.push_frame(pc["TextFrame"](text=voice_text))
                            await self.push_frame(pc["LLMFullResponseEndFrame"]())
                            voice_pushed = True

                    if not event_waiter.done():
                        event_waiter.cancel()

                except Exception:
                    logger.exception("ChatProcessor: error processing transcription")
                    if not voice_pushed:
                        await self.push_frame(pc["LLMFullResponseStartFrame"]())
                        await self.push_frame(
                            pc["TextFrame"](text="Sorry, I encountered an error processing that.")
                        )
                        await self.push_frame(pc["LLMFullResponseEndFrame"]())
            else:
                await self.push_frame(frame, direction)

    return ChatProcessor()


def create_stt():
    """Create MLX Whisper STT optimized for Apple Silicon."""
    pc = _import_pipecat()
    return pc["WhisperSTTServiceMLX"](
        model=pc["MLXModel"].LARGE_V3_TURBO,
        language=pc["Language"].EN,
        no_speech_prob=0.4,
        temperature=0.0,
    )


def create_tts(voice_id: str = "af_heart"):
    """Create Kokoro TTS service."""
    pc = _import_pipecat()
    return pc["KokoroTTSService"](voice_id=voice_id)


def create_transport(websocket: Any):
    """Create a FastAPI WebSocket transport for a single connection."""
    pc = _import_pipecat()
    return pc["FastAPIWebsocketTransport"](
        websocket=websocket,
        params=pc["FastAPIWebsocketParams"](
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=pc["SileroVADAnalyzer"](
                params=pc["VADParams"](stop_secs=0.6),
            ),
            serializer=pc["ProtobufFrameSerializer"](),
        ),
    )


async def run_voice_pipeline(transport, stt, tts, chat_processor=None) -> None:
    """Run the voice pipeline: mic → VAD → STT → ChatProcessor → TTS → speaker."""
    pc = _import_pipecat()
    processors = [transport.input(), stt]
    if chat_processor:
        processors.append(chat_processor)
    processors.extend([tts, transport.output()])

    pipeline = pc["Pipeline"](processors)
    task = pc["PipelineTask"](pipeline, params=pc["PipelineParams"](allow_interruptions=True))
    runner = pc["PipelineRunner"]()
    await runner.run(task)
