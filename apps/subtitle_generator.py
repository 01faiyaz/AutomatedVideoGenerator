import os
import re


def format_time(seconds: float) -> str:
    """Convert float seconds to SRT timestamp: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def create_subtitles(script: str, scene_duration: float = None) -> str:
    """
    Split the script into sentences and assign timestamps.
    scene_duration: seconds per subtitle card (defaults to SCENE_DURATION env var or 4s).
    """
    if scene_duration is None:
        scene_duration = float(os.getenv("SCENE_DURATION", "4"))

    # Split on sentence-ending punctuation
    sentences = re.split(r"(?<=[.!?])\s+", script.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    srt_blocks = []
    start = 0.0

    for i, sentence in enumerate(sentences, start=1):
        # Slightly longer cards for longer sentences
        word_count = len(sentence.split())
        duration = max(scene_duration, word_count * 0.4)  # ~0.4s per word minimum
        end = start + duration

        srt_blocks.append(
            f"{i}\n"
            f"{format_time(start)} --> {format_time(end)}\n"
            f"{sentence}\n"
        )

        start = end

    srt_content = "\n".join(srt_blocks)

    path = "outputs/subtitles.srt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    print(f"[subtitles] Generated {len(sentences)} subtitle cards → {path}")
    return path
