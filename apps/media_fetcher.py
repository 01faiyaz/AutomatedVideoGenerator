import os
import requests
from dotenv import load_dotenv

load_dotenv()


def fetch_video_for_scene(query: str, scene_number: int) -> str:
    """Try Pexels first, fall back to Pixabay."""
    pexels_key = os.getenv("PEXELS_API_KEY", "")
    pixabay_key = os.getenv("PIXABAY_API_KEY", "")

    if pexels_key and pexels_key != "your_pexels_key_here":
        try:
            return fetch_pexels_video(query, scene_number, pexels_key)
        except Exception as e:
            print(f"[media] Pexels failed for '{query}': {e}. Trying Pixabay...")

    if pixabay_key and pixabay_key != "your_pixabay_key_here":
        try:
            return fetch_pixabay_video(query, scene_number, pixabay_key)
        except Exception as e:
            print(f"[media] Pixabay failed for '{query}': {e}. Using placeholder...")

    # Last resort: create a solid-color placeholder clip via FFmpeg
    return create_placeholder_clip(scene_number, query)


def fetch_pexels_video(query: str, scene_number: int, api_key: str) -> str:
    response = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": api_key},
        params={
            "query": query,
            "per_page": 5,
            "orientation": os.getenv("VIDEO_ORIENTATION", "landscape")
        },
        timeout=30
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("videos"):
        raise Exception(f"No Pexels video found for query: '{query}'")

    # Pick the best quality file that's reasonably sized
    video_files = data["videos"][0]["video_files"]
    # Prefer HD (1280x720) or closest to it
    video_files_sorted = sorted(
        video_files,
        key=lambda f: abs((f.get("width", 0) * f.get("height", 0)) - (1280 * 720))
    )
    video_url = video_files_sorted[0]["link"]

    return _download_video(video_url, scene_number)


def fetch_pixabay_video(query: str, scene_number: int, api_key: str) -> str:
    response = requests.get(
        "https://pixabay.com/api/videos/",
        params={
            "key": api_key,
            "q": query,
            "per_page": 5,
            "video_type": "film"
        },
        timeout=30
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("hits"):
        raise Exception(f"No Pixabay video found for query: '{query}'")

    videos = data["hits"][0]["videos"]
    # Prefer medium quality
    video_url = (
        videos.get("medium", {}).get("url")
        or videos.get("small", {}).get("url")
        or videos.get("large", {}).get("url")
    )

    if not video_url:
        raise Exception("No usable video URL from Pixabay response")

    return _download_video(video_url, scene_number)


def _download_video(url: str, scene_number: int) -> str:
    output_path = f"media/scene_{scene_number}.mp4"
    print(f"[media] Downloading scene {scene_number}: {url[:60]}...")

    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"[media] Scene {scene_number} saved to {output_path}")
    return output_path


def create_placeholder_clip(scene_number: int, label: str = "") -> str:
    """Generate a 5-second solid color clip using FFmpeg as a placeholder."""
    import subprocess

    output_path = f"media/scene_{scene_number}.mp4"
    color = ["0x1a1a2e", "0x16213e", "0x0f3460", "0x533483", "0xe94560"][scene_number % 5]
    duration = int(os.getenv("SCENE_DURATION", "5"))

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={color}:size=1280x720:duration={duration}:rate=24",
        "-vf", f"drawtext=text='{label[:30]}':fontcolor=white:fontsize=32:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264",
        output_path
    ], check=True, capture_output=True)

    print(f"[media] Created placeholder clip for scene {scene_number}")
    return output_path
