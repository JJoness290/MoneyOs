import asyncio
import hashlib
import random
import re
from dataclasses import dataclass
from pathlib import Path

import edge_tts
from pydub import AudioSegment, effects, silence

from app.config import DEFAULT_VOICE

FADE_MS = 5
MIN_SILENCE_MS = 200
MAX_SILENCE_MS = 350


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


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _generate_sentence_audio(
    text: str,
    output_path: Path,
    voice: str,
    rate: str | None,
    pitch: str | None,
) -> None:
    async def _run() -> None:
        settings: dict[str, str] = {}
        if rate:
            settings["rate"] = rate
        if pitch:
            settings["pitch"] = pitch
        communicate = edge_tts.Communicate(
            text,
            voice=voice,
            **settings,
        )
        await communicate.save(str(output_path))

    asyncio.run(_run())


def _apply_fades(segment: AudioSegment) -> AudioSegment:
    return segment.fade_in(FADE_MS).fade_out(FADE_MS)


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

    chunk_durations: list[float] = []
    combined = AudioSegment.silent(duration=0)
    seen_hashes: set[str] = set()

    for index, sentence in enumerate(sentences):
        chunk_path = output_path.with_name(f"{output_path.stem}_chunk{index}.mp3")
        print(f"TTS sentence {index + 1}/{len(sentences)}")
        try:
            _generate_sentence_audio(
                sentence,
                chunk_path,
                voice,
                rate=_random_rate(),
                pitch=_random_pitch(),
            )
        except Exception:
            if chunk_path.exists():
                chunk_path.unlink()
            print("TTS retry with neutral settings")
            _generate_sentence_audio(
                sentence,
                chunk_path,
                voice,
                rate=None,
                pitch=None,
            )

        if not chunk_path.exists():
            raise RuntimeError("TTS failed to generate audio for sentence.")

        chunk_hash = _hash_file(chunk_path)
        if chunk_hash in seen_hashes:
            raise RuntimeError("Repeated audio detected in TTS output.")
        seen_hashes.add(chunk_hash)

        segment = AudioSegment.from_file(chunk_path)
        segment = _apply_fades(segment)
        chunk_durations.append(segment.duration_seconds)

        if len(combined) == 0:
            combined = segment
        else:
            combined = combined.append(segment, crossfade=FADE_MS)

        silence_duration = random.randint(MIN_SILENCE_MS, MAX_SILENCE_MS)
        silence_segment = AudioSegment.silent(duration=silence_duration)
        combined = combined.append(silence_segment, crossfade=FADE_MS)

        chunk_path.unlink(missing_ok=True)

    combined = effects.normalize(combined)
    combined = _remove_micro_silences(combined)
    combined.export(output_path, format="mp3")

    final_audio = AudioSegment.from_file(output_path)
    final_duration = final_audio.duration_seconds

    expected_total = sum(chunk_durations) + (len(sentences) * MIN_SILENCE_MS / 1000.0)
    if final_duration < expected_total - 0.5:
        raise RuntimeError("Final audio appears truncated.")
    if expected_seconds is not None and final_duration < expected_seconds:
        raise RuntimeError("Generated audio is shorter than expected script length.")

    return TTSResult(
        audio_path=output_path,
        duration_seconds=final_duration,
        chunk_count=len(sentences),
        chunk_durations=chunk_durations,
    )
