from dataclasses import dataclass
import json
import random
from pathlib import Path
from typing import Tuple

import numpy as np
from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, VideoFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

from app.config import MINECRAFT_BG_DIR, TARGET_FPS, TARGET_RESOLUTION


@dataclass
class VideoBuildResult:
    output_path: Path
    duration_seconds: float


def _fit_background(clip: VideoFileClip) -> VideoFileClip:
    target_w, target_h = TARGET_RESOLUTION
    clip = clip.resize(height=target_h) if clip.h < target_h else clip.resize(height=target_h)
    if clip.w < target_w:
        clip = clip.resize(width=target_w)
    x_center = clip.w / 2
    y_center = clip.h / 2
    return clip.crop(
        x_center=x_center,
        y_center=y_center,
        width=target_w,
        height=target_h,
    )


def _usage_path() -> Path:
    return MINECRAFT_BG_DIR / ".usage.json"


def _load_usage_history() -> dict[str, list[tuple[float, float]]]:
    path = _usage_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    history: dict[str, list[tuple[float, float]]] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                segments: list[tuple[float, float]] = []
                for entry in value:
                    if isinstance(entry, list) and len(entry) == 2:
                        segments.append((float(entry[0]), float(entry[1])))
                history[str(key)] = segments
    return history


def _save_usage_history(history: dict[str, list[tuple[float, float]]]) -> None:
    payload = {key: segments[-200:] for key, segments in history.items()}
    _usage_path().write_text(json.dumps(payload), encoding="utf-8")


def _ensure_background_clips() -> list[Path]:
    if not MINECRAFT_BG_DIR.exists() or not MINECRAFT_BG_DIR.is_dir():
        raise RuntimeError(
            "NO MINECRAFT BACKGROUND FOUND.\n"
            "Place at least one video in assets/minecraft/\n"
            "Generation has been aborted."
        )
    backgrounds = sorted(MINECRAFT_BG_DIR.glob("*.mp4"))
    if not backgrounds:
        raise RuntimeError(
            "NO MINECRAFT BACKGROUND FOUND.\n"
            "Place at least one video in assets/minecraft/\n"
            "Generation has been aborted."
        )
    return backgrounds


def _segments_overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> bool:
    return max(a_start, b_start) < min(a_end, b_end)


def _select_segment(
    clip_duration: float,
    segment_duration: float,
    used_segments: list[tuple[float, float]],
    attempts: int = 30,
) -> tuple[float, float] | None:
    if clip_duration <= segment_duration:
        start, end = 0.0, min(clip_duration, segment_duration)
        if any(_segments_overlap(start, end, used_start, used_end) for used_start, used_end in used_segments):
            return None
        return start, end
    for _ in range(attempts):
        start = random.uniform(0, clip_duration - segment_duration)
        end = start + segment_duration
        if any(_segments_overlap(start, end, used_start, used_end) for used_start, used_end in used_segments):
            continue
        return start, end
    return None


def _load_background(audio_duration: float) -> VideoFileClip:
    backgrounds = _ensure_background_clips()
    usage = _load_usage_history()
    rng = random.Random()
    remaining = audio_duration
    clips: list[VideoFileClip] = []
    attempts = 0
    max_attempts = max(10, len(backgrounds) * 30)

    while remaining > 0 and attempts < max_attempts:
        attempts += 1
        path = rng.choice(backgrounds)
        clip = VideoFileClip(str(path)).without_audio()
        clip = _fit_background(clip)
        if clip.duration <= 0:
            clip.close()
            continue

        segment_duration = min(remaining, rng.uniform(20, 60))
        used_segments = usage.get(str(path), [])
        selection = _select_segment(clip.duration, segment_duration, used_segments)
        if selection is None:
            clip.close()
            continue

        start, end = selection
        used_segments.append((start, end))
        usage[str(path)] = used_segments
        clips.append(clip.subclip(start, end))
        remaining -= (end - start)

    if remaining > 0:
        for clip in clips:
            clip.close()
        raise RuntimeError("Available background footage is shorter than audio.")

    _save_usage_history(usage)
    return concatenate_videoclips(clips, method="compose")


def _chunk_subtitles(text: str, min_words: int = 2, max_words: int = 6) -> list[str]:
    words = [word for word in text.split() if word.strip()]
    chunks = []
    index = 0
    rng = random.Random(7)
    while index < len(words):
        chunk_size = rng.randint(min_words, max_words)
        chunk = words[index : index + chunk_size]
        chunks.append(" ".join(chunk))
        index += chunk_size
    return chunks


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _subtitle_clip(text: str, duration: float, resolution: Tuple[int, int]) -> ImageClip:
    width, height = resolution
    font = _load_font(size=64)
    padding = 24
    max_width = width - padding * 2

    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    words = text.split()
    lines: list[str] = []
    current = []
    for word in words:
        test_line = " ".join(current + [word])
        line_width = draw.textlength(test_line, font=font)
        if line_width <= max_width:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    total_height = sum(font.getbbox(line)[3] for line in lines) + (len(lines) - 1) * 8
    y = height - 180 - total_height
    for line in lines:
        line_width = draw.textlength(line, font=font)
        x = (width - line_width) / 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0, 200))
        y += font.getbbox(line)[3] + 8

    return ImageClip(np.array(image)).set_duration(duration)


def _build_subtitles(text: str, duration: float) -> list[ImageClip]:
    chunks = _chunk_subtitles(text)
    if not chunks:
        return []
    per_chunk = duration / len(chunks)
    clips = []
    start = 0.0
    for chunk in chunks:
        clip = _subtitle_clip(chunk, per_chunk, TARGET_RESOLUTION)
        clip = clip.set_start(start)
        clips.append(clip)
        start += per_chunk
    return clips


def build_video(
    script_text: str,
    audio_path: Path,
    output_path: Path,
) -> VideoBuildResult:
    audio_clip = AudioFileClip(str(audio_path))
    audio_duration = float(audio_clip.duration)
    if audio_duration <= 0:
        audio_clip.close()
        raise RuntimeError("Audio duration is zero.")
    if audio_duration > 1200:
        print("Warning: Video render may take a long time for extended durations.")
    background = _load_background(audio_duration)
    subtitle_clips = _build_subtitles(script_text, audio_duration)
    layers = [background] + subtitle_clips

    final_video = CompositeVideoClip(layers, size=TARGET_RESOLUTION)
    final_video = final_video.set_duration(audio_duration)
    final_video = final_video.set_audio(audio_clip)

    final_video.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac",
        fps=TARGET_FPS,
        threads=4,
        preset="medium",
        temp_audiofile=str(output_path.with_suffix(".temp-audio.m4a")),
        remove_temp=True,
    )

    background.close()
    audio_clip.close()

    return VideoBuildResult(output_path=output_path, duration_seconds=audio_duration)
