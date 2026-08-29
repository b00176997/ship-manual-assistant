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

# Sizes verified against the Ollama registry. The search model (bge-large) also
# lives on the GPU (~1.4 GB), so leave that much headroom when choosing.
# (minimum VRAM in GB, ollama model, download size)
CHOICES = [
    (11.0, "qwen3:14b", "9.3 GB"),   # fits fully in 12 GB+, best quality/speed balance
    (7.0, "qwen3:8b", "5.2 GB"),     # comfortable on 8 GB cards
    (0.0, "qwen2.5:7b", "4.7 GB"),   # fallback / CPU
]

# Bigger models that do NOT fit entirely in 16 GB: Ollama puts the overflow in
# system RAM, so they run slower but answer better. Offered as an experiment.
BIGGER = [
    ("qwen3.6:27b", "17.8 GB", "256K context, needs ~3 GB of RAM offload on a 16 GB card"),
    ("qwen3.6:35b", "22.6 GB", "strongest option here, but the slowest on a 16 GB card"),
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
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    dry = "--dry-run" in sys.argv
    print()
    if not shutil.which("ollama"):
        print("  Ollama is not installed - install it from https://ollama.com/download")
        print("  and run setup.bat again.")
        return 1

    vram = detect_vram_gb()
    if args:
        model, size = args[0], "custom"
        print(f"  Requested model          : {model}")
    else:
        model, size = pick(vram)
    print(f"  Graphics memory detected : {vram:.0f} GB")
    print(f"  Current offline model    : {config.OLLAMA_MODEL}")
    print(f"  Best fit for this card   : {model}  ({size} download)")
    print()
    if not args:
        print("  Want to try something bigger? These do not fit fully in 16 GB, so")
        print("  part of the model runs from system RAM - slower, but stronger:")
        for name, sz, note in BIGGER:
            print(f"    {name:<16} {sz:>8}   {note}")
        print(f"  To use one:  upgrade_offline_model.bat {BIGGER[0][0]}")
        print()

    if model == config.OLLAMA_MODEL:
        print("  You are already using that model. Nothing to do.")
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
