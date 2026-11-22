import pymupdf as pdf


def _extract_pdf(path: Path) -> str:
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
