"""Upgrade the offline (Ollama) model to one that suits this GPU.

The default is a 7B model so it fits any 8 GB card. On a 12 GB+ card a 14B model
fits and answers noticeably better, so this script picks the best fit, downloads
it, and records the choice in .env.

Run via upgrade_offline_model.bat. Use --dry-run to see the plan without downloading.
"""
import re
import shutil
import subprocess
import sys

import config

# (minimum free VRAM in GB, ollama model, approximate download)
CHOICES = [
    (12.0, "qwen2.5:14b", "~9 GB"),
    (0.0, "qwen2.5:7b", "~5 GB"),
]


def detect_vram_gb():
    try:
        import torch

        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / 1e9
    except Exception:
        pass
    return 0.0


def pick(vram):
    for need, model, size in CHOICES:
        if vram >= need:
            return model, size
    return CHOICES[-1][1], CHOICES[-1][2]


def set_env_model(model):
    """Write OLLAMA_MODEL into .env, replacing any existing setting."""
    env = config.BASE_DIR / ".env"
    lines = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    out, replaced = [], False
    for ln in lines:
        if re.match(r"\s*#?\s*OLLAMA_MODEL\s*=", ln):
            if not replaced:
                out.append(f"OLLAMA_MODEL={model}")
                replaced = True
            continue  # drop duplicates / commented variants
        out.append(ln)
    if not replaced:
        out.append(f"OLLAMA_MODEL={model}")
    env.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    dry = "--dry-run" in sys.argv
    print()
    if not shutil.which("ollama"):
        print("  Ollama is not installed - install it from https://ollama.com/download")
        print("  and run setup.bat again.")
        return 1

    vram = detect_vram_gb()
    model, size = pick(vram)
    print(f"  Graphics memory detected : {vram:.0f} GB")
    print(f"  Current offline model    : {config.OLLAMA_MODEL}")
    print(f"  Best fit for this card   : {model}  ({size} download)")
    print()

    if model == config.OLLAMA_MODEL:
        print("  You are already using the best model for this card. Nothing to do.")
        return 0

    if dry:
        print("  [dry run] would download the model and write OLLAMA_MODEL to .env")
        return 0

    print(f"  Downloading {model} - this takes a while, please wait...")
    print()
    rc = subprocess.call(["ollama", "pull", model])
    if rc != 0:
        print()
        print(f"  Download failed (code {rc}). Nothing was changed.")
        return rc

    set_env_model(model)
    print()
    print(f"  Done. The offline model is now {model}.")
    print("  Close the program and start it again (start.bat) to use it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
