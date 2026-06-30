import os
import sys
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()


def generate_voiceover(script: str) -> str:
    provider = os.getenv("TTS_PROVIDER", "system").lower()

    if provider == "elevenlabs":
        return _elevenlabs_tts(script)
    elif provider == "piper":
        return _piper_tts(script)
    else:
        return _system_tts(script)


def _system_tts(script: str) -> str:
    platform = sys.platform
    if platform == "darwin":
        return _macos_say(script)
    elif platform == "win32":
        return _windows_tts(script)
    else:
        return _espeak_tts(script)


def _windows_tts(script: str) -> str:
    wav_path = "outputs/voiceover.wav"
    mp3_path = "outputs/voiceover.mp3"

    # Use pyttsx3 if available, otherwise fall back to PowerShell SAPI
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 155)   # speaking speed
        engine.setProperty("volume", 1.0)
        # Try to pick a decent voice
        voices = engine.getProperty("voices")
        for v in voices:
            if "zira" in v.name.lower() or "david" in v.name.lower():
                engine.setProperty("voice", v.id)
                break
        engine.save_to_file(script, wav_path)
        engine.runAndWait()
        print("[tts] pyttsx3 voiceover generated")
    except ImportError:
        # Fallback: PowerShell SAPI
        ps_script = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.SetOutputToWaveFile('{wav_path}'); "
            f"$s.Speak([System.IO.File]::ReadAllText('outputs/tts_input.txt')); "
            f"$s.Dispose()"
        )
        with open("outputs/tts_input.txt", "w", encoding="utf-8") as f:
            f.write(script)
        subprocess.run(["powershell", "-Command", ps_script], check=True)
        print("[tts] PowerShell SAPI voiceover generated")

    # Convert WAV → MP3
    subprocess.run([
        "ffmpeg", "-y", "-i", wav_path, mp3_path
    ], check=True, capture_output=True)

    return mp3_path


def _macos_say(script: str) -> str:
    aiff_path = "outputs/voiceover.aiff"
    mp3_path = "outputs/voiceover.mp3"
    subprocess.run(["say", "-o", aiff_path, script], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", aiff_path, mp3_path],
                   check=True, capture_output=True)
    print("[tts] macOS 'say' voiceover generated")
    return mp3_path


def _espeak_tts(script: str) -> str:
    wav_path = "outputs/voiceover.wav"
    mp3_path = "outputs/voiceover.mp3"
    subprocess.run(["espeak-ng", "-w", wav_path, "-s", "150", "-a", "150", script], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", wav_path, mp3_path],
                   check=True, capture_output=True)
    print("[tts] espeak-ng voiceover generated")
    return mp3_path


def _piper_tts(script: str) -> str:
    wav_path = "outputs/voiceover.wav"
    mp3_path = "outputs/voiceover.mp3"
    model = os.getenv("PIPER_MODEL", "en_US-amy-medium.onnx")
    subprocess.run(["piper", "--model", model, "--output_file", wav_path],
                   input=script.encode("utf-8"), check=True)
    subprocess.run(["ffmpeg", "-y", "-i", wav_path, mp3_path],
                   check=True, capture_output=True)
    print("[tts] Piper TTS voiceover generated")
    return mp3_path


def _elevenlabs_tts(script: str) -> str:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    if not api_key or api_key == "your_elevenlabs_key_here":
        raise Exception("ELEVENLABS_API_KEY not set in .env")

    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={
            "text": script,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        },
        timeout=60
    )
    response.raise_for_status()

    mp3_path = "outputs/voiceover.mp3"
    with open(mp3_path, "wb") as f:
        f.write(response.content)
    print("[tts] ElevenLabs voiceover generated")
    return mp3_path
