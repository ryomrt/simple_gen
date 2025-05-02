import os, uuid, datetime
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, Form, File
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .prompt_loader import load_prompts
from .file_utils import extract_text_from_file
from .llm_client import run_llm, LLM_PROVIDER  # ← LLM_PROVIDERをimport
from .whisper_client import transcribe_audio

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
PROMPTS = load_prompts(BASE_DIR.parent / "prompts.yaml")

import re

def extract_html_from_markdown(text: str) -> str:
    """
    Markdownの ```html ... ``` コードブロックからHTML部分だけを抽出する
    """
    # re.DOTALLで改行も含めてマッチ
    match = re.search(r"```html\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text  # マッチしなければ元のテキストを返す

def sanitize_filename(name: str) -> str:
    import os
    base, ext = os.path.splitext(name)
    safe_base = "".join(c for c in base if c.isalnum() or c in ("-", "_"))[:50]
    safe_ext = ext if ext else ""
    return safe_base + safe_ext

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    tmpl = env.get_template("index.html")
    return tmpl.render(prompts=PROMPTS)

@app.post("/submit")
async def submit(
    request: Request,
    prompt_name: str = Form(...),
    text_input: str = Form(""),
    file: UploadFile | None = File(None)
):
    selected = next((p for p in PROMPTS if p.name == prompt_name), None)
    if not selected:
        return JSONResponse({"error": "Invalid prompt"}, status_code=400)

    content = text_input or ""
    file_path = None
    if file and file.filename:
        tmp_path = OUTPUT_DIR / (str(uuid.uuid4()) + "_" + sanitize_filename(file.filename))
        with tmp_path.open("wb") as f:
            f.write(await file.read())
        file_path = tmp_path

    # OpenAI: テキスト抽出して渡す
    # Gemini: ファイルがあればファイルパスを渡す
    if LLM_PROVIDER == "openai":
        if file_path:
            extracted, is_text = extract_text_from_file(file_path)
            content = extracted
        if not content:
            return JSONResponse({"error": "No input provided"}, status_code=400)
        result = run_llm(selected.system_prompt, content)
    elif LLM_PROVIDER == "gemini":
        # テキスト入力があればそれを、なければファイルパスを渡す
        if not content and not file_path:
            return JSONResponse({"error": "No input provided"}, status_code=400)
        result = run_llm(selected.system_prompt, content, file_path)
    else:
        return JSONResponse({"error": "Unsupported LLM provider"}, status_code=400)

    ext_result = result if selected.output_format.lower().startswith("md") else extract_html_from_markdown(result)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = ".md" if selected.output_format.lower().startswith("md") else ".html"
    out_path = OUTPUT_DIR / f"{prompt_name}_{timestamp}{ext}"
    out_path.write_text(ext_result, encoding="utf-8")

    download_url = f"/download/{out_path.name}"
    return JSONResponse({"download_url": download_url})

@app.get("/download/{filename}")
async def download(filename: str):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(path, filename=filename)

@app.post("/upload-audio")
async def upload_audio(file: UploadFile):
    audio_bytes = await file.read()
    text = await transcribe_audio(audio_bytes, file.filename)
    return {"text": text}