"""Bulk load: index every PDF in the manuals/ folder at once.
Already-indexed files are skipped, so you can drop in new manuals and re-run.
Pass --force to re-index everything from scratch.

Run:  python ingest_folder.py        (or double-click index_manuals.bat)
      python ingest_folder.py --force
      python ingest_folder.py path/to/folder
"""
import sys
from pathlib import Path

import config
from ingest import ingest_pdf, list_sources


def main():
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    folder = Path(args[0]) if args else config.MANUALS_DIR

    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in folder: {folder}")
        return

    already = set()
    if not force:
        srcs, _ = list_sources()
        already = {s["source"] for s in srcs}

    print(f"Found {len(pdfs)} PDF(s). Indexing...\n")
    indexed = skipped = 0
    for pdf in pdfs:
        if pdf.name in already:
            print(f"-  {pdf.name}: already indexed, skipping")
            skipped += 1
            continue
        print(f"-> {pdf.name}")
        result = ingest_pdf(pdf, source_name=pdf.name)
        if result.get("warning"):
            print(f"   WARNING: {result['warning']}")
        else:
            extra = " (text recovered via OCR)" if result.get("ocr_used") else ""
            print(f"   done, chunks: {result['chunks']}{extra}")
            indexed += 1

    print(f"\nDone. Indexed {indexed} new file(s), skipped {skipped} already-indexed.")
    if skipped and not force:
        print("Tip: run with --force to rebuild everything from scratch.")


if __name__ == "__main__":
    main()
