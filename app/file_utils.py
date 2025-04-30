import base64, mimetypes, io
from pathlib import Path
from typing import Tuple
from pdfminer.high_level import extract_text as pdf_extract
import docx

TEXT_EXT = {'.txt', '.md'}

def extract_text_from_file(path: Path) -> Tuple[str, bool]:
    ext = path.suffix.lower()
    if ext in TEXT_EXT:
        return path.read_text(encoding="utf-8", errors="ignore"), True
    elif ext == '.pdf':
        return pdf_extract(str(path)), True
    elif ext == '.docx':
        doc = docx.Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs), True
    else:
        # Unsupported binary: return base64
        b64 = base64.b64encode(path.read_bytes()).decode()
        return f"(base64) {b64}", False