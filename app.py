"""Local web app: upload manuals and ask questions about them."""
import traceback
from pathlib import Path

from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

import config
import costs
import settings
import translator
from ingest import (
    ingest_pdf,
    list_sources,
    delete_source,
    index_status,
    reindex_all,
    IndexModelMismatch,
)
from rag import answer

settings.load_and_apply()  # apply the saved search depth to config at startup

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # up to 200 MB per file


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/status")
def status():
    sources, total = list_sources()
    idx = index_status()
    return jsonify(
        {
            "sources": sources,
            "total_chunks": total,
            "has_key": bool(config.ANTHROPIC_API_KEY),
            "index": idx,
            "today": costs.today(),
            "depth": settings.get_depth(),
        }
    )


@app.route("/settings", methods=["POST"])
def update_settings():
    data = request.get_json(force=True)
    try:
        applied = settings.set_depth(data.get("depth"))
        return jsonify({"ok": True, "depth": applied})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/reindex", methods=["POST"])
def reindex():
    try:
        results = reindex_all()
        total = sum(r.get("chunks", 0) for r in results)
        return jsonify({"ok": True, "files": len(results), "chunks": total})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Re-index failed: {e}"}), 500


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file received"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty file name"}), 400
    if not f.filename.lower().endswith(".pdf"):
        return jsonify({"error": "A PDF file is required"}), 400

    filename = secure_filename(f.filename)
    save_path = config.MANUALS_DIR / filename
    f.save(str(save_path))

    try:
        result = ingest_pdf(save_path, source_name=filename)
        return jsonify(result)
    except IndexModelMismatch as e:
        return jsonify({"error": str(e), "mismatch": True}), 409
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Processing error: {e}"}), 500


@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_json(force=True)
    source = data.get("source")
    if not source:
        return jsonify({"error": "No file specified"}), 400
    delete_source(source)
    # also delete the PDF itself from disk (basename only — never escape manuals/)
    pdf = config.MANUALS_DIR / secure_filename(source)
    if pdf.exists():
        try:
            pdf.unlink()
        except Exception:
            pass
    return jsonify({"ok": True})


@app.route("/translate", methods=["POST"])
def translate():
    """Free-form translate / rewrite / format, always on the local model."""
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Nothing to translate"}), 400
    if not translator.is_available():
        return jsonify({
            "error": "The local AI is not running. Start Ollama (and make sure the "
                     f"model {config.OLLAMA_MODEL} is installed), then try again."
        }), 503
    try:
        return jsonify({"result": translator.translate(text), "model": config.OLLAMA_MODEL})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Translation failed: {type(e).__name__}"}), 500


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True)
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Empty question"}), 400
    try:
        return jsonify(answer(question))
    except IndexModelMismatch as e:
        return jsonify({"error": str(e), "mismatch": True}), 409
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error: {e}"}), 500


if __name__ == "__main__":
    print("\n=== Ship Mechanic Assistant ===")
    print("Open in your browser:  http://127.0.0.1:5000\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
