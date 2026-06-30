# AI Video Generator

A local, self-hosted pipeline that converts a text topic into a complete MP4 video with voiceover, subtitles, and metadata. No cloud video services required.

**Input:** A topic string.  
**Output:** `final_video.mp4`, `subtitles.srt`, title, description, thumbnail text.

---

## Architecture

```
index.html
    |
    v
n8n (webhook)
    |
    v
FastAPI (Python)
    |-- script_generator.py  -->  Ollama / OpenAI
    |-- media_fetcher.py     -->  Pexels / Pixabay
    |-- voice_generator.py   -->  system TTS / ElevenLabs / Piper
    |-- subtitle_generator.py
    |-- video_assembler.py   -->  FFmpeg
    |
    v
outputs/final_video.mp4
outputs/subtitles.srt
```

---

## Prerequisites

| Tool | Notes |
|------|-------|
| Python 3.11+ | https://python.org |
| Docker Desktop | Required for n8n |
| FFmpeg | `winget install "FFmpeg (Essentials Build)"` on Windows, `brew install ffmpeg` on macOS |
| Ollama (optional) | https://ollama.com — free local AI |

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/your-username/ai-video-generator.git
cd ai-video-generator
```

**2. Configure environment variables**

```bash
cp .env.example .env
```

Open `.env` and fill in your API keys. At minimum you need a Pexels key (free at https://pexels.com/api).

**3. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**4. Start Ollama** (skip if using OpenAI)

```bash
ollama pull llama3.1
ollama serve
```

**5. Start n8n**

```bash
docker compose up -d
```

Open http://localhost:5678, then go to **Settings > Import Workflow** and import `n8n_workflow.json`.

**6. Start the API server**

```bash
uvicorn app.main:app --reload --port 8000
```

**7. Open the web form**

Open `index.html` in your browser.

---

## Usage

### Web form

Open `index.html`, enter a topic, click **Generate Video**, and wait 60-120 seconds.

### Direct API

```bash
curl -X POST http://localhost:8000/generate-video \
  -H "Content-Type: application/json" \
  -d '{"topic":"5 facts about black holes"}'
```

### n8n webhook

```bash
curl -X POST http://localhost:5678/webhook/generate-video \
  -H "Content-Type: application/json" \
  -d '{"topic":"5 facts about black holes"}'
```

### Response

```json
{
  "status": "complete",
  "elapsed_seconds": 65.0,
  "video_path": "outputs/final_video.mp4",
  "subtitle_path": "outputs/subtitles.srt",
  "title": "Solar Panels Explained",
  "description": "Learn how solar panels harness sunlight...",
  "thumbnail_text": "Solar Panels Explained"
}
```

Output files are written to the `outputs/` directory.

---

## Configuration

All options are set in `.env`.

| Variable | Default | Description |
|----------|---------|-------------|
| `PEXELS_API_KEY` | — | Required. Free at pexels.com/api |
| `PIXABAY_API_KEY` | — | Optional fallback media source |
| `USE_OLLAMA` | `true` | `true` = local Ollama, `false` = OpenAI |
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | Must be `localhost`, not `host.docker.internal` |
| `OLLAMA_MODEL` | `llama3.1` | Any model pulled via `ollama pull` |
| `OPENAI_API_KEY` | — | Required only if `USE_OLLAMA=false` |
| `TTS_PROVIDER` | `system` | `system`, `elevenlabs`, or `piper` |
| `ELEVENLABS_API_KEY` | — | Required only if `TTS_PROVIDER=elevenlabs` |
| `SCENE_DURATION` | `5` | Fallback seconds per scene (overridden by voiceover length) |

---

## Voice Providers

| Provider | Quality | Cost | Platform |
|----------|---------|------|----------|
| `system` | Acceptable | Free | Windows (pyttsx3 / SAPI), macOS (say), Linux (espeak-ng) |
| `elevenlabs` | Excellent | Paid | All |
| `piper` | Good | Free | All (requires manual install) |

**Windows users:** Install pyttsx3 for the system provider:

```bash
pip install pyttsx3
```

**Linux users:**

```bash
sudo apt install espeak-ng
```

---

## Project Structure

```
ai-video-generator/
├── docker-compose.yml
├── .env.example
├── .env                    # not committed
├── requirements.txt
├── n8n_workflow.json
├── index.html
├── app/
│   ├── main.py
│   ├── generator.py
│   ├── script_generator.py
│   ├── media_fetcher.py
│   ├── voice_generator.py
│   ├── subtitle_generator.py
│   └── video_assembler.py
├── media/                  # not committed
├── outputs/                # not committed
├── music/
├── scripts/
└── n8n_data/               # not committed
```

---

## Planned Improvements

- Subtitle burn-in on Windows (currently delivered as a separate SRT)
- Voiceover-synced scene timing per sentence
- 9:16 vertical video mode
- Background music layering
- Thumbnail image generation
- Job queue for concurrent requests
- YouTube / TikTok publishing

---
