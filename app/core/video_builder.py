from dataclasses import dataclass
from pathlib import Path

from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips
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


def build_video(
    broll_paths: list[Path],
    audio_path: Path,
    output_path: Path,
) -> VideoBuildResult:
    if not broll_paths:
        raise RuntimeError("No B-roll clips available to build video.")

    with AudioFileClip(str(audio_path)) as audio_clip:
        audio_duration = float(audio_clip.duration)

        clips = []
        current_time = 0.0
        clip_index = 0
        while current_time < audio_duration and clip_index < len(broll_paths):
            path = broll_paths[clip_index]
            clip_index += 1
            with VideoFileClip(str(path)) as raw_clip:
                clip = _fit_to_vertical(raw_clip)
                clip_duration = min(clip.duration, audio_duration - current_time)
                if clip_duration <= 0:
                    continue
                trimmed = clip.subclip(0, clip_duration)
                clips.append(trimmed)
                current_time += clip_duration

        if current_time < audio_duration:
            raise RuntimeError("Not enough B-roll to cover full audio duration.")

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
