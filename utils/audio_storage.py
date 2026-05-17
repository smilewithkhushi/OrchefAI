import os
from datetime import datetime

AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "audio")


def save_audio(audio_bytes: bytes, event_id: str | None = None) -> str:
    os.makedirs(AUDIO_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = event_id or "new"
    filename = f"{prefix}_{ts}.wav"
    filepath = os.path.join(AUDIO_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(audio_bytes)
    return filepath
