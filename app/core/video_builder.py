from dataclasses import dataclass
import math
import random
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, VideoClip
from PIL import Image, ImageDraw, ImageFont

from app.config import TARGET_FPS, TARGET_RESOLUTION


@dataclass
class VideoBuildResult:
    output_path: Path
    duration_seconds: float


def _generate_platforms(seed: int, count: int, spacing: float) -> list[dict]:
    rng = random.Random(seed)
    platforms = []
    for index in range(count):
        platforms.append(
            {
                "offset": index * spacing,
                "width": rng.uniform(0.3, 0.65),
                "height": rng.uniform(0.03, 0.07),
                "x": rng.uniform(-0.4, 0.4),
                "color": (
                    rng.randint(120, 220),
                    rng.randint(120, 220),
                    rng.randint(120, 220),
                ),
            }
        )
    return platforms


def _render_frame(
    t: float,
    duration: float,
    resolution: Tuple[int, int],
    platforms: list[dict],
    loop_length: float,
) -> np.ndarray:
    width, height = resolution
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:] = (18, 18, 22)

    speed = loop_length / max(duration, 1.0)
    bob = int(math.sin(t * 3.2) * 6)

    for platform in platforms:
        z = (platform["offset"] - t * speed) % loop_length
        depth = z / loop_length
        perspective = 1.0 - depth
        if perspective <= 0:
            continue
        y = int(height * 0.15 + (1 - depth) * height * 0.85) + bob
        block_w = int(width * platform["width"] * (0.3 + 0.7 * perspective))
        block_h = int(height * platform["height"] * (0.3 + 0.7 * perspective))
        center_x = int(width * 0.5 + platform["x"] * width * 0.5)
        x1 = max(0, center_x - block_w // 2)
        x2 = min(width, center_x + block_w // 2)
        y1 = max(0, y - block_h // 2)
        y2 = min(height, y + block_h // 2)
        color = platform["color"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness=-1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (10, 10, 10), thickness=2)

    return frame


def _procedural_background(duration: float) -> VideoClip:
    resolution = TARGET_RESOLUTION
    loop_length = max(6.0, min(12.0, duration))
    platform_count = 120
    spacing = loop_length / 18
    platforms = _generate_platforms(seed=42, count=platform_count, spacing=spacing)

    def make_frame(t: float) -> np.ndarray:
        return _render_frame(t, duration, resolution, platforms, loop_length)

    return VideoClip(make_frame=make_frame, duration=duration).set_fps(TARGET_FPS)


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
    y = height - 260 - total_height
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
    with AudioFileClip(str(audio_path)) as audio_clip:
        audio_duration = float(audio_clip.duration)
        background = _procedural_background(audio_duration)
        subtitle_clips = _build_subtitles(script_text, audio_duration)
        layers = [background] + subtitle_clips

        final_video = CompositeVideoClip(layers, size=TARGET_RESOLUTION)
        final_video = final_video.set_audio(audio_clip)
        final_video = final_video.set_duration(audio_duration)

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

        return VideoBuildResult(output_path=output_path, duration_seconds=audio_duration)
