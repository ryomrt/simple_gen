from pathlib import Path
import yaml
from pydantic import BaseModel
from typing import List

class Prompt(BaseModel):
    name: str
    title: str
    system_prompt: str
    output_format: str = "markdown"

def load_prompts(file_path: Path) -> List[Prompt]:
    raw = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    return [Prompt(**item) for item in raw]