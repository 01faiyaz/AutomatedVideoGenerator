import os
import time
from app.script_generator import generate_script
from app.media_fetcher import fetch_video_for_scene
from app.voice_generator import generate_voiceover
from app.subtitle_generator import create_subtitles
from app.video_assembler import assemble_video


def generate_video(topic: str) -> dict:
    start_time = time.time()
    print(f"\n{'='*50}")
    print(f"[generator] Starting video generation for: {topic}")
    print(f"{'='*50}")

    # Ensure output directories exist
    os.makedirs("media", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)

    # Step 1: Generate script and metadata
    print("\n[generator] Step 1/5: Generating script...")
    data = generate_script(topic)
    print(f"[generator] Title: {data['title']}")
    print(f"[generator] Scenes: {len(data['scenes'])}")

    # Step 2: Fetch media for each scene
    print("\n[generator] Step 2/5: Fetching stock media...")
    media_files = []
    for scene in data["scenes"]:
        keywords = " ".join(scene["visual_keywords"])
        print(f"  Scene {scene['scene_number']}: searching for '{keywords}'")
        path = fetch_video_for_scene(keywords, scene["scene_number"])
        media_files.append(path)

    # Step 3: Generate voiceover
    print("\n[generator] Step 3/5: Generating voiceover...")
    voiceover_path = generate_voiceover(data["script"])

    # Step 4: Generate subtitles
    print("\n[generator] Step 4/5: Generating subtitles...")
    subtitles_path = create_subtitles(data["script"])

    # Step 5: Assemble final video
    print("\n[generator] Step 5/5: Assembling video with FFmpeg...")
    video_path = assemble_video(media_files, voiceover_path, subtitles_path)

    elapsed = round(time.time() - start_time, 1)
    print(f"\n[generator] ✅ Done in {elapsed}s")

    return {
        "status": "complete",
        "elapsed_seconds": elapsed,
        "video_path": video_path,
        "subtitle_path": subtitles_path,
        "title": data["title"],
        "description": data["description"],
        "thumbnail_text": data["thumbnail_text"]
    }
