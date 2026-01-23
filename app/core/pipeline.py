from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.config import AUDIO_DIR, MIN_AUDIO_SECONDS, VIDEO_DIR
from app.core.script_gen import ScriptResult, expand_script_once, generate_script, sanitize_script
from app.core.tts import TTSResult, generate_tts
from app.core.video_builder import VideoBuildResult, build_video


@dataclass
class PipelineResult:
    script: ScriptResult
    tts: TTSResult
    video: VideoBuildResult


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _build_audio_path() -> Path:
    return AUDIO_DIR / f"tts_{_timestamp()}.mp3"


def _build_video_path() -> Path:
    return VIDEO_DIR / f"moneyos_{_timestamp()}.mp4"


def run_pipeline(status_callback) -> PipelineResult:
    status_callback("Generating script...")
    script = generate_script(min_seconds=MIN_AUDIO_SECONDS)
    if script.estimated_seconds < MIN_AUDIO_SECONDS:
        script = expand_script_once(script.text)
    sanitized_script = sanitize_script(script.text)

    status_callback("Generating script...")
    audio_path = _build_audio_path()
    tts_result = generate_tts(sanitized_script, audio_path)
    status_callback(
        "TTS chunks="
        f"{tts_result.chunk_count} | chunk_durations={tts_result.chunk_durations} | "
        f"final_audio={tts_result.duration_seconds:.2f}s | "
        f"estimated={tts_result.estimated_seconds:.2f}s"
    )
    if tts_result.duration_seconds < MIN_AUDIO_SECONDS:
        raise RuntimeError("Generated audio is shorter than 60 seconds.")

    status_callback("Rendering video...")
    video_path = _build_video_path()
    video_result = build_video(sanitized_script, tts_result.audio_path, video_path)

    status_callback(
        f"Done (audio: {tts_result.duration_seconds:.2f}s, video: {video_result.duration_seconds:.2f}s)"
    )
    return PipelineResult(script=script, tts=tts_result, video=video_result)
