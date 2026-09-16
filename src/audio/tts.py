from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
import urllib.request
import wave
from pathlib import Path


class GeminiTTSProvider:
    endpoint = "https://generativelanguage.googleapis.com/v1beta/interactions"

    def __init__(self, model: str, voice: str, api_key: str | None = None) -> None:
        self.model, self.voice = model, voice
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    def synthesize(self, text: str, output_path: Path) -> None:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        payload = {"model": self.model, "input": text, "response_format": {"type": "audio"}, "generation_config": {"speech_config": [{"voice": self.voice}]}}
        request = urllib.request.Request(self.endpoint, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key}, method="POST")
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
        try:
            pcm = base64.b64decode(body["output_audio"]["data"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("Gemini TTS returned no audio data") from exc
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="literary-daily-tts-") as temp_dir:
            wav_path = Path(temp_dir) / "audio.wav"
            with wave.open(str(wav_path), "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(24000)
                wav_file.writeframes(pcm)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path), "-codec:a", "libmp3lame", "-b:a", "96k", str(output_path)], check=True, timeout=180)


def generate_audio(provider: GeminiTTSProvider, text: str, output_path: Path, retries: int = 2) -> bool:
    for attempt in range(retries + 1):
        try:
            provider.synthesize(text, output_path)
            return True
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            if attempt == retries:
                print(f"[TTS] failed after {retries + 1} attempts: {type(exc).__name__}")
    return False
