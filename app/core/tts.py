import asyncio
from dataclasses import dataclass
from pathlib import Path

import edge_tts
from moviepy.audio.fx.all import audio_normalize
from moviepy.editor import AudioFileClip

from app.config import DEFAULT_VOICE, TTS_RATE


@dataclass
class TTSResult:
    audio_path: Path
    duration_seconds: float


def _get_audio_duration(audio_path: Path) -> float:
    from moviepy.editor import AudioFileClip

    with AudioFileClip(str(audio_path)) as clip:
        return float(clip.duration)


def synthesize_speech(text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> TTSResult:
    async def _run() -> None:
        communicate = edge_tts.Communicate(text, voice=voice, rate=TTS_RATE)
        await communicate.save(str(output_path))

    asyncio.run(_run())
    with AudioFileClip(str(output_path)) as clip:
        normalized = audio_normalize(clip).volumex(1.05)
        normalized.write_audiofile(str(output_path), logger=None)
        normalized.close()
    duration = _get_audio_duration(output_path)
    return TTSResult(audio_path=output_path, duration_seconds=duration)
