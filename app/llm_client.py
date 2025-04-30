from typing import Dict
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()

def run_llm(system_prompt: str, user_content: str) -> str:
    chat_completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )
    return chat_completion.choices[0].message.content