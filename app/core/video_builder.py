from dataclasses import dataclass
import random
from pathlib import Path
from typing import Tuple

import numpy as np
from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, VideoFileClip, vfx
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


def _load_background(audio_duration: float) -> VideoFileClip:
    backgrounds = sorted(MINECRAFT_BG_DIR.glob("*.mp4"))
    if not backgrounds:
        raise RuntimeError("No Minecraft background videos found in assets/minecraft.")
    bg_path = random.choice(backgrounds)
    bg = VideoFileClip(str(bg_path)).without_audio()
    bg = _fit_background(bg)
    if bg.duration >= audio_duration:
        bg = bg.subclip(0, audio_duration)
    else:
        bg = bg.fx(vfx.loop, duration=audio_duration)
    return bg


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

        return VideoBuildResult(output_path=output_path, duration_seconds=audio_duration)
