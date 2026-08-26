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
            line(OK, "Graphics card (GPU)", f"{name} - working, indexing will be fast")
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

        names = [m["name"] for m in json.loads(r.read().decode()).get("models", [])]
    want = config.OLLAMA_MODEL
    if want in names:
        line(OK, "Offline AI (Ollama)", f"{want} ready")
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
print("=" * 62)
print()
