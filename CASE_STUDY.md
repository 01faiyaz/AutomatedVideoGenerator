# Case Study: Building an AI Video Generator MVP

## Overview

This document covers the build and debugging process for a local AI video generation pipeline. The system takes a text topic as input and outputs a complete MP4 with voiceover and subtitle files. It was built from a spec document and debugged entirely on a Windows machine.

**Stack:** Python, FastAPI, FFmpeg, n8n, Ollama, Pexels API, pyttsx3  
**Time to working MVP:** Approximately 2 hours including all debugging  
**Platform:** Windows 11

---

## Build Process

The system was built in phases following a specification document:

1. Python modules written first (`script_generator`, `media_fetcher`, `voice_generator`, `subtitle_generator`, `video_assembler`)
2. FastAPI server wrapping the pipeline
3. n8n workflow connecting a webhook to the FastAPI endpoint
4. Web form as the front-end interface

The decision to build the Python engine first before wiring up n8n proved correct. Isolating the video pipeline made each error easier to identify and fix.

---

## Errors Encountered and Fixes Applied

### 1. Wrong working directory for uvicorn

**Error:** `ModuleNotFoundError: No module named 'app'`  
**Cause:** `uvicorn app.main:app` was run from `C:\Windows\System32` instead of the project root. Python could not find the `app` package.  
**Fix:** Always `cd` into the project folder before running uvicorn. The command must be run from `ai-video-generator/`.

---

### 2. Ollama connection refused

**Error:** `Could not connect to Ollama`  
**Cause:** The `.env` file had `OLLAMA_URL=http://host.docker.internal:11434/api/generate`. This hostname only resolves from inside a Docker container. The FastAPI server was running directly on Windows, where Ollama is accessible at `localhost`.  
**Fix:** Changed `OLLAMA_URL` to `http://localhost:11434/api/generate`.

---

### 3. AI response missing required field: scenes

**Error:** `AI response missing required field: 'scenes'`  
**Cause:** `llama3.1` returned valid JSON but omitted the `scenes` array. The original prompt left too much room for the model to abbreviate its output.  
**Fix:** Two changes to `script_generator.py`:
- Added `"format": "json"` to the Ollama request body, which activates Ollama's JSON output mode and forces structurally valid responses
- Added a fallback function `_ensure_scenes()` that auto-generates scenes from the script text if the model omits them, so the pipeline never hard-fails on this step

---

### 4. ElevenLabs 401 Unauthorized

**Error:** `401 Client Error: Unauthorized for url: https://api.elevenlabs.io/v1/text-to-speech/...`  
**Cause:** The ElevenLabs API key in `.env` was invalid.  
**Fix:** Switched `TTS_PROVIDER` to `system` and installed `pyttsx3`, which uses Windows' built-in speech synthesis (SAPI) with no API key required. The voice generator was updated to detect the OS and route to the correct backend: `pyttsx3` on Windows, `say` on macOS, `espeak-ng` on Linux.

---

### 5. FFmpeg subtitle filter failing on Windows

**Error:** `Command [...subtitles=C:\\Users\\...\\subtitles.srt...] returned non-zero exit status 4294967274`  
**Cause:** FFmpeg's `subtitles` filter does not accept Windows-style paths. Backslashes and the drive letter colon (`C:`) in the path caused the filter to fail at the argument parsing stage.  
**Fix:** On Windows, the subtitle burn-in step is skipped entirely. The video is assembled with audio only, and `subtitles.srt` is delivered as a separate file alongside the MP4. Both files can be loaded together in VLC or uploaded to YouTube as a caption track. A path-escaping helper function (`_escape_srt_path`) was also added for potential future use on non-Windows systems.

---

### 6. Video cutting off before audio ends

**Error:** Video ended early; the last several seconds of voiceover had no corresponding video.  
**Cause:** Scene duration was set to a fixed 5 seconds per scene (25 seconds total for 5 scenes). The generated voiceover was longer than 25 seconds, and the `-shortest` FFmpeg flag cut the output to the video length.  
**Fix:** The assembler now measures the voiceover duration with `ffprobe` before building anything, then divides that duration evenly across the number of scenes. Each stock clip is looped or trimmed to that calculated per-scene duration, so the concatenated video always matches the audio length before they are merged.

---

## Outcome

The MVP reached a working state with all core functionality intact:

- Topic input via web form
- AI-generated script, title, description, and thumbnail text via Ollama
- Stock video clips fetched from Pexels
- Voiceover generated using Windows system TTS
- SRT subtitle file generated and time-aligned to the script
- Final MP4 assembled by FFmpeg with audio and video in sync

A test generation for the topic "how solar panels work" completed in 65 seconds.

---

## Lessons

- Run the Python engine standalone before introducing n8n. Every error in this build was in the Python layer; n8n was never the problem.
- Local LLMs need JSON output mode explicitly enabled. Prompting alone is not reliable enough for structured output.
- FFmpeg path handling on Windows is a known compatibility issue. Delivering the SRT separately is a cleaner solution than fighting the subtitle filter escaping.
- Always match video duration to audio duration by measuring the audio first, not by assuming a fixed clip length.
