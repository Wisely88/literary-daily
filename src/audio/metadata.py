from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


def audio_metadata(path: Path) -> dict[str, str | int | None]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    duration: int | None = None
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], capture_output=True, text=True, check=True, timeout=20)
        duration = round(float(result.stdout.strip()))
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return {"checksum": digest, "duration_seconds": duration}
