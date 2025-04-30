import os, httpx
from dotenv import load_dotenv
load_dotenv()

WHISPER_URL = os.getenv("WHISPER_URL", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

async def transcribe_audio(file_bytes: bytes, filename: str) -> str:
    if not WHISPER_URL:
        return ""
    
    # OpenAI公式APIの場合
    if "api.openai.com" in WHISPER_URL:
        if not OPENAI_API_KEY:
            return ""
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        data = {
            "model": "whisper-1"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                WHISPER_URL,
                headers=headers,
                data=data,
                files={"file": (filename, file_bytes, "audio/wav")}
            )
            resp.raise_for_status()
            return resp.json().get("text", "")
    
    # 自前サーバーの場合（APIキー不要、パラメータもシンプル）
    else:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                WHISPER_URL,
                files={"file": (filename, file_bytes, "audio/wav")}
            )
            resp.raise_for_status()
            return resp.json().get("text", "")