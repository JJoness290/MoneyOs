import asyncio
import random
import re
from dataclasses import dataclass
from pathlib import Path

import edge_tts
from moviepy.editor import AudioClip, AudioFileClip, concatenate_audioclips

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
    rate = random.uniform(0.96, 1.04)
    percent = int(round((rate - 1.0) * 100))
    sign = "+" if percent >= 0 else ""
    return f"{sign}{percent}%"


def _random_pitch() -> str:
    percent = random.uniform(0.1, 3.0)
    sign = random.choice(["+", "-"])
    return f"{sign}{percent:.1f}%"


def _generate_sentence_audio(text: str, output_path: Path, voice: str) -> float:
    async def _run() -> None:
        communicate = edge_tts.Communicate(
            text,
            voice=voice,
            rate=_random_rate(),
            pitch=_random_pitch(),
        )
        await communicate.save(str(output_path))

    asyncio.run(_run())
    audio = AudioFileClip(str(output_path))
    duration = float(audio.duration)
    audio.close()
    return duration


def generate_tts(script_text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> TTSResult:
    sentences = split_script_for_tts(script_text)
    if not sentences:
        raise RuntimeError("Script text is empty after splitting.")

    chunk_paths: list[Path] = []
    chunk_durations: list[float] = []
    clips = []

    for index, sentence in enumerate(sentences):
        chunk_path = output_path.with_name(f"{output_path.stem}_chunk{index}.mp3")
        duration = _generate_sentence_audio(sentence, chunk_path, voice)
        chunk_paths.append(chunk_path)
        chunk_durations.append(duration)
        clips.append(AudioFileClip(str(chunk_path)))
        silence_duration = random.uniform(0.2, 0.4)
        clips.append(AudioClip(lambda t: 0.0, duration=silence_duration, fps=44100))

    final_audio = concatenate_audioclips(clips)
    final_audio.write_audiofile(str(output_path), logger=None)
    final_audio.close()
    for clip in clips:
        clip.close()

    final = AudioFileClip(str(output_path))
    final_duration = float(final.duration)
    final.close()
    for path in chunk_paths:
        if path.exists():
            path.unlink()

    return TTSResult(
        audio_path=output_path,
        duration_seconds=final_duration,
        chunk_count=len(sentences),
        chunk_durations=chunk_durations,
    )
