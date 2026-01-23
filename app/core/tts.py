import asyncio
import random
import re
from dataclasses import dataclass
from pathlib import Path

import edge_tts
from pydub import AudioSegment, effects, silence

from app.config import DEFAULT_VOICE


@dataclass
class TTSResult:
    audio_path: Path
    duration_seconds: float
    chunk_count: int
    chunk_durations: list[float]


def split_script_for_tts(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    return sentences


def _random_rate() -> str:
    percent = random.uniform(-5.0, 5.0)
    sign = "+" if percent >= 0 else ""
    return f"{sign}{percent:.1f}%"


def _random_pitch() -> str:
    percent = random.uniform(-3.0, 3.0)
    sign = "+" if percent >= 0 else ""
    return f"{sign}{percent:.1f}%"


def _generate_tts_audio(text: str, output_path: Path, voice: str, rate: str, pitch: str) -> None:
    async def _run() -> None:
        communicate = edge_tts.Communicate(
            text,
            voice=voice,
            rate=rate,
            pitch=pitch,
        )
        await communicate.save(str(output_path))

    asyncio.run(_run())


def _remove_micro_silences(segment: AudioSegment) -> AudioSegment:
    if segment.dBFS == float("-inf"):
        threshold = -45.0
    else:
        threshold = min(-45.0, segment.dBFS - 16)
    ranges = silence.detect_silence(segment, min_silence_len=1, silence_thresh=threshold)
    micro_ranges = [r for r in ranges if (r[1] - r[0]) < 10]
    for start_ms, end_ms in reversed(micro_ranges):
        segment = segment[:start_ms] + segment[end_ms:]
    return segment


def generate_tts(
    script_text: str,
    output_path: Path,
    voice: str = DEFAULT_VOICE,
    expected_seconds: float | None = None,
) -> TTSResult:
    sentences = split_script_for_tts(script_text)
    if not sentences:
        raise RuntimeError("Script text is empty after splitting.")

    rate = _random_rate()
    pitch = _random_pitch()
    _generate_tts_audio(script_text, output_path, voice, rate=rate, pitch=pitch)

    audio = AudioSegment.from_file(output_path)
    audio = effects.normalize(audio)
    audio = _remove_micro_silences(audio)
    audio.export(output_path, format="mp3")

    final_audio = AudioSegment.from_file(output_path)
    final_duration = final_audio.duration_seconds

    if expected_seconds is not None:
        min_expected = expected_seconds * 0.9
        max_expected = expected_seconds * 1.1
        if final_duration < min_expected:
            raise RuntimeError("Generated audio is shorter than expected script length.")
        if final_duration > max_expected:
            raise RuntimeError("Generated audio is longer than expected script length.")

    return TTSResult(
        audio_path=output_path,
        duration_seconds=final_duration,
        chunk_count=1,
        chunk_durations=[final_duration],
    )
