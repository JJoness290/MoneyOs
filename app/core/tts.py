import asyncio
from dataclasses import dataclass
from pathlib import Path

import edge_tts
from moviepy.editor import AudioFileClip

from app.config import DEFAULT_VOICE, TTS_RATE


@dataclass
class TTSResult:
    audio_path: Path
    duration_seconds: float


def _estimate_seconds(text: str) -> float:
    word_count = len(text.split())
    return word_count / 2.2


def generate_tts(script_text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> TTSResult:
    """
    Generates full audio from text in ONE pass.
    Returns duration in seconds.
    """
    async def _run() -> None:
        communicate = edge_tts.Communicate(script_text, voice=voice, rate=TTS_RATE)
        await communicate.save(str(output_path))

    asyncio.run(_run())

    audio = AudioFileClip(str(output_path))
    duration = float(audio.duration)
    audio.close()

    if duration <= 1:
        raise RuntimeError("Generated audio is too short or invalid")
    if duration < 30:
        raise RuntimeError("Generated audio is too short for TikTok length requirements")

    expected = _estimate_seconds(script_text)
    if duration + 1 < expected:
        raise RuntimeError("Generated audio appears truncated compared to script length")

    return TTSResult(audio_path=output_path, duration_seconds=duration)
