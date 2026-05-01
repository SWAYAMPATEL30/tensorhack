import base64
import os
import tempfile
import subprocess
from transformers import pipeline

print("Loading Whisper STT Model. This might take a moment...")
stt_pipeline = pipeline("automatic-speech-recognition", model="openai/whisper-tiny")

def transcribe_audio(base64_payload: str) -> str:
    """
    Accepts a base64 audio payload (with optional data-URI prefix).
    Detects MIME type from the prefix, writes to temp file, transcribes.
    """
    # Detect mime type before stripping
    suffix = ".webm"
    if base64_payload.startswith("data:"):
        header = base64_payload.split(";")[0].lower()
        if "mp4" in header:    suffix = ".mp4"
        elif "ogg" in header:  suffix = ".ogg"
        elif "wav" in header:  suffix = ".wav"
        elif "webm" in header: suffix = ".webm"
        # Strip the data URI header
        base64_payload = base64_payload.split(",")[1]

    print(f"DEBUG STT: Received audio chunk. Suffix={suffix}, b64_len={len(base64_payload)}")

    try:
        audio_bytes = base64.b64decode(base64_payload)
    except Exception as e:
        print(f"STT Error: Failed to decode base64: {e}")
        return ""

    if len(audio_bytes) < 100:
        print("STT Warning: Audio chunk too small, skipping.")
        return ""

    # Write to temp file
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmpfile.write(audio_bytes)
    tmpfile.close()
    tmp_path = tmpfile.name
    wav_path = tmp_path.replace(suffix, ".wav")

    try:
        # Convert to WAV using ffmpeg for maximum compatibility
        ffmpeg_available = False
        try:
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", tmp_path, "-ar", "16000", "-ac", "1", "-f", "wav", wav_path],
                capture_output=True, timeout=15
            )
            ffmpeg_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        target_path = wav_path if ffmpeg_available and os.path.exists(wav_path) else tmp_path
        print(f"DEBUG STT: Transcribing from {target_path} (ffmpeg={ffmpeg_available})")

        transcription = stt_pipeline(target_path)
        text = transcription.get("text", "").strip()
        print(f"DEBUG STT: Transcribed: '{text}'")
        return text

    except Exception as e:
        print(f"STT Error during transcription: {e}")
        return ""
    finally:
        for path in [tmp_path, wav_path]:
            if os.path.exists(path):
                try: os.remove(path)
                except: pass
