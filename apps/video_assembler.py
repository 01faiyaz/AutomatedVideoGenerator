import os
import sys
import subprocess
import json


def get_duration(path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def normalize_clip(input_path: str, output_path: str, target_duration: float) -> str:
    subprocess.run([
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", input_path,
        "-t", str(target_duration),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,"
               "pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-r", "24",
        "-c:v", "libx264",
        "-preset", "fast",
        "-an",
        output_path
    ], check=True, capture_output=True)
    return output_path


def assemble_video(
    media_files: list,
    voiceover_path: str,
    subtitles_path: str
) -> str:

    # Measure voiceover so video matches it exactly
    voiceover_duration = get_duration(voiceover_path)
    num_scenes = len(media_files)
    scene_duration = voiceover_duration / num_scenes
    print(f"[video] Voiceover: {voiceover_duration:.1f}s → {scene_duration:.1f}s per scene")

    # Step 1: Normalize all clips to the per-scene duration
    print("[video] Normalizing clips...")
    normalized = []
    for i, path in enumerate(media_files):
        norm_path = f"outputs/norm_{i}.mp4"
        normalize_clip(path, norm_path, scene_duration)
        normalized.append(norm_path)

    # Step 2: Write concat list
    clips_file = "outputs/clips.txt"
    with open(clips_file, "w", encoding="utf-8") as f:
        for path in normalized:
            abs_path = os.path.abspath(path).replace("\\", "/")
            f.write(f"file '{abs_path}'\n")

    # Step 3: Concatenate silent video
    silent_path = "outputs/silent_video.mp4"
    print("[video] Concatenating clips...")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", clips_file,
        "-c:v", "libx264",
        "-preset", "fast",
        silent_path
    ], check=True, capture_output=True)

    # Step 4: Merge audio — pad video if needed, no -shortest
    output_path = "outputs/final_video.mp4"
    print("[video] Adding audio...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", silent_path,
        "-i", voiceover_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "128k",
        # Use audio duration as master; extend video with last frame if needed
        "-vf", "tpad=stop_mode=clone:stop_duration=5",
        "-shortest",
        output_path
    ], check=True, capture_output=True)

    # Cleanup
    for path in normalized:
        try: os.remove(path)
        except OSError: pass
    try: os.remove(silent_path)
    except OSError: pass

    print(f"[video] Final video → {output_path}")
    return output_path
