from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

# OpenAI
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-2025-04-14")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Gemini
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def run_llm(system_prompt: str, user_content: str, file_path: str = None) -> str:
    if LLM_PROVIDER == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        chat_completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
        )
        return chat_completion.choices[0].message.content

    elif LLM_PROVIDER == "gemini":
        # ここからSDK利用に書き換え
        from google import genai
        import pathlib

        client = genai.Client(api_key=GEMINI_API_KEY)

        if file_path:
            file_path = pathlib.Path(file_path)
            # MIMEタイプ自動判定
            ext = file_path.suffix.lower()
            if ext == ".pdf":
                mime_type = "application/pdf"
            elif ext == ".docx":
                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif ext == ".txt":
                mime_type = "text/plain"
            elif ext == ".md":
                mime_type = "text/markdown"
            else:
                mime_type = "application/octet-stream"  # ← 不明な場合はこれ
            
            # ファイルアップロード
            sample_file = client.files.upload(
                file=file_path,
                config=dict(mime_type=mime_type) if mime_type else None
            )
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[sample_file, f"{system_prompt}\n{user_content}"]
            )
            return response.text
        else:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[f"{system_prompt}\n{user_content}"]
            )
            return response.text

    else:
        raise ValueError("サポートされていないLLM_PROVIDERです")