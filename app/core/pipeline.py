import math
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.config import AUDIO_DIR, MIN_AUDIO_SECONDS, VIDEO_DIR
from app.core import broll_selector
from app.core.pexels import PexelsClient
from app.core.script_gen import ScriptResult, generate_script
from app.core.tts import TTSResult, synthesize_speech
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


def _gather_broll(script: str, min_clips: int) -> list[Path]:
    client = PexelsClient()
    segments = broll_selector.split_script(script)
    query_sets = broll_selector.build_query_sets(segments)
    generic_fallbacks = [
        "hands typing",
        "city motion",
        "phone closeup",
        "people walking street",
        "office overtime",
    ]

    collected: list[Path] = []
    used_ids: set[int] = set()

    for queries in query_sets:
        for query in queries:
            candidates = client.search_videos(query)
            random.shuffle(candidates)
            for candidate in candidates:
                if candidate.video_id in used_ids:
                    continue
                used_ids.add(candidate.video_id)
                downloaded = client.download_videos([candidate])
                collected.extend(downloaded)
                if len(collected) >= min_clips:
                    return collected

    while len(collected) < min_clips:
        fallback_query = random.choice(generic_fallbacks)
        candidates = client.search_videos(fallback_query)
        random.shuffle(candidates)
        for candidate in candidates:
            if candidate.video_id in used_ids:
                continue
            used_ids.add(candidate.video_id)
            downloaded = client.download_videos([candidate])
            collected.extend(downloaded)
            if len(collected) >= min_clips:
                return collected

    return collected


def run_pipeline(status_callback) -> PipelineResult:
    status_callback("Generating script...")
    script = generate_script(min_seconds=MIN_AUDIO_SECONDS)

    status_callback("Generating script...")
    audio_path = _build_audio_path()
    tts_result = synthesize_speech(script.text, audio_path)

    if tts_result.duration_seconds < MIN_AUDIO_SECONDS:
        status_callback("Generating script...")
        script = generate_script(min_seconds=MIN_AUDIO_SECONDS + 10)
        tts_result = synthesize_speech(script.text, audio_path)

    status_callback("Downloading B-roll...")
    min_clips = max(12, math.ceil(tts_result.duration_seconds / 1.6))
    broll_paths = _gather_broll(script.text, min_clips)

    if len(broll_paths) < min_clips:
        status_callback("Downloading B-roll...")
        broll_paths = _gather_broll(script.text, min_clips + 4)

    status_callback("Rendering video...")
    video_path = _build_video_path()
    video_result = build_video(broll_paths, tts_result.audio_path, video_path)

    if abs(video_result.duration_seconds - tts_result.duration_seconds) > 0.1:
        status_callback("Rendering video...")
        video_result = build_video(broll_paths, tts_result.audio_path, video_path)

    status_callback("Done")
    return PipelineResult(script=script, tts=tts_result, video=video_result)
