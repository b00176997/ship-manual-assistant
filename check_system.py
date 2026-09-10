"""System check: verifies that everything needed is installed and actually works.
Run it via check_system.bat and send a screenshot if something is wrong."""
import shutil
import sys
import urllib.request

OK, BAD, WARN = "[ OK ]", "[FAIL]", "[note]"


def line(status, label, detail=""):
    print(f" {status}  {label:<26} {detail}")


print()
print("=" * 62)
print(" SHIP MECHANIC ASSISTANT - SYSTEM CHECK")
print("=" * 62)

problems = []
vram_gb = 0.0

# --- Python ---
v = sys.version_info
line(OK if v[:2] == (3, 12) else WARN, "Python", f"{v.major}.{v.minor}.{v.micro}")

# --- GPU / PyTorch ---
try:
    import torch

    line(OK, "PyTorch", torch.__version__)
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        # is_available() alone is not proof: a mismatched CUDA build reports True
        # but every kernel launch fails. Run a real operation to be sure.
        try:
            (torch.randn(64, 64, device="cuda") @ torch.randn(64, 64, device="cuda")).sum().item()
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 2**30
            line(OK, "Graphics card (GPU)", f"{name}, {vram_gb:.0f} GB - working")
        except Exception as e:
            line(BAD, "Graphics card (GPU)", f"{name} - NOT usable ({type(e).__name__})")
            problems.append("The GPU is detected but PyTorch cannot use it. "
                            "Run update.bat - it installs the right GPU support.")
    else:
        line(WARN, "Graphics card (GPU)", "not used - running on CPU (indexing will be slow)")
except Exception as e:
    line(BAD, "PyTorch", f"not working ({type(e).__name__})")
    problems.append("PyTorch is broken - run setup.bat again.")

# --- Search model / index ---
try:
    import config

    line(OK, "Search model", config.EMBEDDING_MODEL)
    line(OK if config.ANTHROPIC_API_KEY else WARN, "Online answers (Claude)",
         "key present" if config.ANTHROPIC_API_KEY else "no key - offline modes only")
    try:
        from ingest import list_sources

        srcs, total = list_sources()
        line(OK, "Loaded manuals", f"{len(srcs)} file(s), {total} chunks")
    except Exception as e:
        line(WARN, "Loaded manuals", f"could not read the index ({type(e).__name__})")
except Exception as e:
    line(BAD, "Program files", f"{type(e).__name__}")
    problems.append("The program files look broken - run setup.bat again.")

# --- Ollama (offline AI) ---
try:
    with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
        import json

        names = {m["name"]: m.get("size", 0)
                 for m in json.loads(r.read().decode()).get("models", [])}
    want = config.OLLAMA_MODEL
    if want in names:
        line(OK, "Offline AI (Ollama)", f"{want} ready")
        # The offline model and the search model share the video memory. A model
        # bigger than the card still works - Ollama runs the overflow on the
        # processor - but answers get slower and the GPU looks only half busy.
        # That confuses people into thinking the card is broken, so say it here.
        size_gb = names[want] / 2**30
        if vram_gb:
            room = vram_gb - 2.0          # the search model keeps about 2 GB
            if size_gb > room:
                line(WARN, "  fits in video memory?",
                     f"no - {size_gb:.0f} GB model, ~{room:.0f} GB free: about "
                     f"{size_gb - room:.0f} GB runs on the processor. Expected "
                     "for this model - offline answers are just slower, nothing "
                     "is broken")
            else:
                line(OK, "  fits in video memory?",
                     f"yes - {size_gb:.0f} GB model, ~{room:.0f} GB free: full GPU speed")
    else:
        line(WARN, "Offline AI (Ollama)", f"running, but {want} is missing")
        problems.append(f"Offline AI needs its model: run  ollama pull {want}")
except Exception:
    if shutil.which("ollama"):
        line(WARN, "Offline AI (Ollama)", "installed but not running - start Ollama")
    else:
        line(WARN, "Offline AI (Ollama)", "not installed - online modes still work")

# --- OCR (scans) ---
line(OK if shutil.which("tesseract") else WARN, "OCR for scanned PDFs",
     "ready" if shutil.which("tesseract") else "not installed - text PDFs still work")

# --- Updates ---
line(OK if shutil.which("git") else WARN, "Updates (Git)",
     "ready - use update.bat" if shutil.which("git") else "not installed - cannot update")

print("=" * 62)
if problems:
    print(" ACTION NEEDED:")
    for p in problems:
        print(f"   - {p}")
else:
    print(" Everything looks good.")
# Asked every time: "why is my graphics card idle?" It is idle most of the day
# by design, because the paid modes answer over the internet.
print()
print(" When the graphics card works: while manuals are being indexed, and")
print(" for the Offline AI and the Translator. Balanced and Thorough send the")
print(" question to Claude over the internet, so the card stays idle then.")
print(" An idle card during a normal question is correct, not a fault.")
print("=" * 62)
print()
