import os, httpx
from dotenv import load_dotenv
load_dotenv()

WHISPER_URL = os.getenv("WHISPER_URL", "")

async def transcribe_audio(file_bytes: bytes, filename: str) -> str:
    if not WHISPER_URL:
        return ""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            WHISPER_URL,
            files={"file": (filename, file_bytes, "audio/wav")}
        )
        resp.raise_for_status()
        return resp.json().get("text", "")