import pymupdf as pdf
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

class ExtractionError(Exception):
    pass

SUPPORTED = {".pdf", ".docx"}
MIN_CHARS=50
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extract_text(path:str|Path)->str:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    ext=path.suffix.lower()
    try:
        if ext==".pdf":
            raw=extract_pdf(path)
        elif ext==".docx":
            raw=extract_pdf(path)
        else:
            raise ExtractionError(f"Unsupported file type: {ext}")
        text=clean_text(raw)

        if len(text) < MIN_CHARS:
            raise ExtractionError("No readable text (scanned or empty file?)")
        return text


    except Exception as e:
        raise ExtractionError(f"Could not read PDF: {e}") from e



def clean_text(text)->str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"-\n(?=[a-z])", "", text)        # rejoin hyphenated line breaks
    text = re.sub(r"[•●▪◦■▶➤]", "-", text)         # unify bullet characters
    text = re.sub(r"[ \t\u00a0]+", " ", text)        # collapse spaces
    text = re.sub(r" *\n *", "\n", text)             # trim around line breaks
    text = re.sub(r"\n{3,}", "\n\n", text)           # at most one blank line
    return text.strip()


def extract_docx(path:str | Path) -> str:
    try:
        with zipfile.ZipFile(path) as z:
            xml_bytes = z.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as e:
        raise ExtractionError(f"Invalid DOCX file: {e}") from e

    root = ET.fromstring(xml_bytes)
    lines = []
    for p in root.iter(f"{W}p"):  
        parts = []
        for node in p.iter():
            if node.tag == f"{W}t" and node.text:
                parts.append(node.text)
            elif node.tag in (f"{W}tab", f"{W}br"):
                parts.append(" ")
        line = "".join(parts).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)



def extract_pdf(path:str | Path) -> str:
    try:
        with pdf.open(path) as doc:
            if doc.needs_pass:
                raise ExtractionError("PDF is password-protected")
            pages = [page.get_text("text", sort=True) for page in doc]

        return "\n\n".join(pages)
        

    except ExtractionError:
        raise
    except Exception as e:
        raise ExtractionError(f"Could not read PDF: {e}") from e


if __name__ == "__main__":
    # Run on one file:  python -m app.parsing.extract data/resume.pdf
    # Run on a folder:  python -m app.parsing.extract data
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "data")

    if target.is_file():
        out = extract_text(target)
        print(f"{len(out)} chars\n")
        print(out[:1500])
    else:
        ok = fail = 0
        for f in sorted(target.iterdir()):
            if f.suffix.lower() in SUPPORTED:
                try:
                    print(f"OK   {f.name}: {len(extract_text(f))} chars")
                    ok += 1
                except Exception as e:
                    print(f"FAIL {f.name}: {e}")
                    fail += 1
        print(f"\n{ok} ok, {fail} failed")

