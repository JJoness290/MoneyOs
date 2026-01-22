from dataclasses import dataclass
from pathlib import Path

from moviepy.editor import AudioFileClip, ColorClip, VideoFileClip, concatenate_videoclips
from moviepy.video.fx.all import crop

from app.config import TARGET_FPS, TARGET_RESOLUTION


@dataclass
class VideoBuildResult:
    output_path: Path
    duration_seconds: float


def _fit_to_vertical(clip: VideoFileClip) -> VideoFileClip:
    target_w, target_h = TARGET_RESOLUTION
    clip = clip.resize(height=target_h) if clip.h < target_h else clip.resize(height=target_h)
    if clip.w < target_w:
        clip = clip.resize(width=target_w)
    x_center = clip.w / 2
    y_center = clip.h / 2
    return crop(clip, width=target_w, height=target_h, x_center=x_center, y_center=y_center)


def _safe_load_clip(path: Path) -> VideoFileClip | None:
    clip = None
    try:
        clip = VideoFileClip(str(path))
    except Exception:
        clip = None
    if clip is not None and clip.duration and clip.duration > 0:
        return clip
    if clip is not None:
        clip.close()
    return None


def _normalize_clips(clips: list[VideoFileClip], audio_duration: float) -> list[VideoFileClip]:
    normalized: list[VideoFileClip] = []
    remaining = audio_duration
    for clip in clips:
        if remaining <= 0:
            break
        usable = min(clip.duration, remaining)
        if usable > 0:
            normalized.append(clip.subclip(0, usable))
            remaining -= usable
    return normalized


def build_video(
    broll_paths: list[Path],
    audio_path: Path,
    output_path: Path,
) -> VideoBuildResult:
    with AudioFileClip(str(audio_path)) as audio_clip:
        audio_duration = float(audio_clip.duration)

        clips: list[VideoFileClip] = []
        current_time = 0.0
        clip_index = 0
        while current_time < audio_duration and clip_index < len(broll_paths):
            path = broll_paths[clip_index]
            clip_index += 1
            raw_clip = _safe_load_clip(path)
            if raw_clip is None:
                continue
            clip = _fit_to_vertical(raw_clip)
            clip_duration = min(clip.duration, audio_duration - current_time)
            if clip_duration <= 0:
                clip.close()
                continue
            clips.append(clip)
            current_time += clip_duration

        if not clips:
            fallback = ColorClip(
                size=TARGET_RESOLUTION,
                color=(0, 0, 0),
                duration=audio_duration,
            )
            clips.append(fallback)

        clips = _normalize_clips(clips, audio_duration)

        if not clips:
            raise RuntimeError("No valid video clips available for rendering")

        final_video = concatenate_videoclips(clips, method="compose")
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
