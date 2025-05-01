import os, uuid, datetime
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, Form, File
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .prompt_loader import load_prompts
from .file_utils import extract_text_from_file
from .llm_client import run_llm
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

def sanitize_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-", "_"))[:50]

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

    # Gather user content
    content = text_input or ""
    if file and file.filename:
        tmp_path = OUTPUT_DIR / (str(uuid.uuid4()) + "_" + sanitize_filename(file.filename))
        with tmp_path.open("wb") as f:
            f.write(await file.read())
        extracted, is_text = extract_text_from_file(tmp_path)
        content = extracted

    if not content:
        return JSONResponse({"error": "No input provided"}, status_code=400)

    result = run_llm(selected.system_prompt, content)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = ".md" if selected.output_format.lower().startswith("md") else ".html"
    out_path = OUTPUT_DIR / f"{prompt_name}_{timestamp}{ext}"
    out_path.write_text(result, encoding="utf-8")

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