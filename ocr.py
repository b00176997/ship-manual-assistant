"""OCR for scanned PDFs: detect image-only manuals and add a text layer so they
can be indexed. Requires the Tesseract engine to be installed on the system;
if it isn't, the system degrades gracefully (the scan is just skipped with a note)."""
import shutil
import config


def is_available():
    """True only if both the ocrmypdf library and the Tesseract engine are present."""
    try:
        import ocrmypdf  # noqa: F401
    except Exception:
        return False
    return shutil.which("tesseract") is not None


def should_ocr(pages):
    """Heuristic: a PDF whose pages yield almost no text is a scan (images only)."""
    if not config.OCR_ENABLED:
        return False
    if not pages:
        return True
    total = sum(len(t.strip()) for _, t in pages)
    # Real text manuals have hundreds+ chars/page; scans yield ~0.
    return total < 80 * len(pages)


def run_ocr(input_path, output_path):
    """Add a searchable text layer to a scanned PDF.
    skip_text=True keeps any existing text and only OCRs the image-only pages."""
    import ocrmypdf
    ocrmypdf.ocr(
        str(input_path),
        str(output_path),
        language=config.OCR_LANGUAGES,
        skip_text=True,
        progress_bar=False,
    )
