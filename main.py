from fastapi import FastAPI, File, HTTPException, UploadFile
import tempfile
from pathlib import Path


from app.parsing.extract import SUPPORTED, ExtractionError, extract_text

app = FastAPI(title="HireLens")
MAX_BYTES = 5 * 1024 * 1024  # 5 MB


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED:
        raise HTTPException(400, f"Only {', '.join(sorted(SUPPORTED))} files are supported")

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "File too large (max 5 MB)")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    try:
        text = extract_text(tmp_path)
    except ExtractionError as e:
        raise HTTPException(422, str(e))
    finally:
        tmp_path.unlink(missing_ok=True)

    return {"filename": file.filename, "chars": len(text), "text": text}