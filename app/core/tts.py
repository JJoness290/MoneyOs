import asyncio
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import edge_tts
from moviepy.editor import AudioFileClip, concatenate_audioclips

from app.config import DEFAULT_VOICE, TTS_RATE


@dataclass
class TTSResult:
    audio_path: Path
    duration_seconds: float
    chunk_count: int
    chunk_durations: list[float]
    estimated_seconds: float


def _estimate_seconds(text: str) -> float:
    word_count = len(text.split())
    return word_count / 2.2


def split_script_for_tts(text: str, max_chars: int = 800) -> list[str]:
    """
    Split on sentence boundaries.
    Never split mid-sentence.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = sentence
    if current:
        chunks.append(current)
    return chunks


def _generate_chunk_audio(text: str, output_path: Path, voice: str) -> float:
    async def _run() -> None:
        communicate = edge_tts.Communicate(text, voice=voice, rate=TTS_RATE)
        await communicate.save(str(output_path))

    asyncio.run(_run())
    audio = AudioFileClip(str(output_path))
    duration = float(audio.duration)
    audio.close()
    if duration <= 1:
        raise RuntimeError("Generated audio chunk is too short or invalid")
    return duration


def generate_tts(script_text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> TTSResult:
    """
    Generates full audio from text in ONE pass.
    Returns duration in seconds.
    """
    char_count = len(script_text)
    max_safe_chars = 800
    if char_count <= max_safe_chars:
        chunks = [script_text]
    else:
        chunks = split_script_for_tts(script_text, max_chars=max_safe_chars)

    chunk_paths: list[Path] = []
    chunk_durations: list[float] = []
    for index, chunk in enumerate(chunks):
        chunk_path = output_path.with_name(f"{output_path.stem}_chunk{index}.mp3")
        duration = _generate_chunk_audio(chunk, chunk_path, voice)
        chunk_paths.append(chunk_path)
        chunk_durations.append(duration)

    if len(chunk_paths) == 1:
        shutil.move(str(chunk_paths[0]), str(output_path))
    else:
        clips = [AudioFileClip(str(path)) for path in chunk_paths]
        final_audio = concatenate_audioclips(clips)
        final_audio.write_audiofile(str(output_path), logger=None)
        final_audio.close()
        for clip in clips:
            clip.close()

    final = AudioFileClip(str(output_path))
    final_duration = float(final.duration)
    final.close()

    expected = _estimate_seconds(script_text)
    if final_duration < expected * 0.9:
        raise RuntimeError("Generated audio appears truncated compared to script length")

    return TTSResult(
        audio_path=output_path,
        duration_seconds=final_duration,
        chunk_count=len(chunks),
        chunk_durations=chunk_durations,
        estimated_seconds=expected,
    )
