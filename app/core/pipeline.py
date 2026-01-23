from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.config import AUDIO_DIR, MIN_AUDIO_SECONDS, SCRIPTS_DIR, VIDEO_DIR
from app.core.script_gen import (
    ScriptResult,
    generate_description,
    generate_script,
    generate_titles,
    sanitize_script,
)
from app.core.tts import TTSResult, generate_tts
from app.core.video_builder import VideoBuildResult, build_video


@dataclass
class PipelineResult:
    script: ScriptResult
    tts: TTSResult
    video: VideoBuildResult
    word_count: int
    titles: list[str]
    description: str


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _build_audio_path(video_id: str) -> Path:
    return AUDIO_DIR / f"tts_{video_id}.mp3"


def _build_video_path(video_id: str) -> Path:
    return VIDEO_DIR / f"moneyos_{video_id}.mp4"


def _build_script_path(video_id: str) -> Path:
    return SCRIPTS_DIR / f"{video_id}.txt"


def run_pipeline(status_callback) -> PipelineResult:
    video_id = _timestamp()
    status_callback("Generating script...")
    print("Script generation started")
    script = generate_script(min_seconds=MIN_AUDIO_SECONDS)
    sanitized_script = sanitize_script(script.text)
    word_count = len(script.text.split())
    titles = generate_titles(script.text)
    description = generate_description(script.text)
    print("Script generation finished")
    print("Generated script:")
    print(script.text)
    script_path = _build_script_path(video_id)
    script_path.write_text(script.text, encoding="utf-8")

    status_callback("Generating TTS...")
    print("TTS generation started")
    audio_path = _build_audio_path(video_id)
    tts_result = generate_tts(sanitized_script, audio_path, expected_seconds=script.estimated_seconds)
    status_callback(
        "TTS chunks="
        f"{tts_result.chunk_count} | chunk_durations={tts_result.chunk_durations} | "
        f"final_audio={tts_result.duration_seconds:.2f}s"
    )
    print(f"Audio duration: {tts_result.duration_seconds:.2f}s")
    if tts_result.duration_seconds < MIN_AUDIO_SECONDS:
        raise RuntimeError("Generated audio is shorter than 600 seconds.")
    print("TTS generation finished")

    status_callback("Rendering video...")
    video_path = _build_video_path(video_id)
    video_result = build_video(sanitized_script, tts_result.audio_path, video_path)

    status_callback(
        f"Done (audio: {tts_result.duration_seconds:.2f}s, video: {video_result.duration_seconds:.2f}s)"
    )
    print(f"Final video duration: {video_result.duration_seconds:.2f}s")
    return PipelineResult(
        script=script,
        tts=tts_result,
        video=video_result,
        word_count=word_count,
        titles=titles,
        description=description,
    )
