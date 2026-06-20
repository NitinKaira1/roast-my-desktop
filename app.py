# app.py
"""
Desktop Court AI — Flask backend.

Simple by design:
- One route serves the page (templates/index.html)
- Three API routes handle the three modes (single / random / all)
- Uploaded images are written to a temp file, sent to Gemini, then deleted
"""

import os
import tempfile

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

from judges import DesktopCourtAI

# ----------------------------
# ENV
# ----------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. Create a .env file with:\n"
        "GEMINI_API_KEY=your_key_here"
    )

ai = DesktopCourtAI(API_KEY)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

# ----------------------------
# APP
# ----------------------------

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_upload_to_tempfile(file_storage) -> str:
    """Saves an uploaded Flask file to a temp path and returns the path."""
    suffix = "." + file_storage.filename.rsplit(".", 1)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        file_storage.save(temp.name)
        return temp.name


def get_uploaded_image_or_error():
    """
    Shared validation for all three endpoints.
    Returns (temp_path, None) on success or (None, (json, status)) on failure.
    """
    if "image" not in request.files:
        return None, (jsonify(error="No image uploaded."), 400)

    file = request.files["image"]

    if file.filename == "":
        return None, (jsonify(error="No image selected."), 400)

    if not allowed_file(file.filename):
        return None, (
            jsonify(error="Unsupported file type. Use PNG, JPG, JPEG, or WEBP."),
            400,
        )

    temp_path = save_upload_to_tempfile(file)
    return temp_path, None


def cleanup(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


# ----------------------------
# ROUTES
# ----------------------------

@app.route("/")
def index():
    return render_template("index.html", judges=ai.get_judge_names())


@app.route("/api/judges")
def api_judges():
    return jsonify(judges=ai.get_judge_names())


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    judge_name = request.form.get("judge_name", "")
    if not judge_name:
        return jsonify(error="No judge selected."), 400

    temp_path, err = get_uploaded_image_or_error()
    if err:
        return err

    try:
        result = ai.run_judge(temp_path, judge_name)
        return jsonify(judge_name=judge_name, result=result)
    except (RuntimeError, ValueError) as exc:
        return jsonify(error=str(exc)), 500
    finally:
        cleanup(temp_path)


@app.route("/api/analyze-random", methods=["POST"])
def api_analyze_random():
    temp_path, err = get_uploaded_image_or_error()
    if err:
        return err

    try:
        judge_name, result = ai.run_random_judge(temp_path)
        return jsonify(judge_name=judge_name, result=result)
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 500
    finally:
        cleanup(temp_path)


@app.route("/api/analyze-all", methods=["POST"])
def api_analyze_all():
    temp_path, err = get_uploaded_image_or_error()
    if err:
        return err

    try:
        result = ai.run_all_judges(temp_path)
        return jsonify(judge_name="All Judges", result=result)
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 500
    finally:
        cleanup(temp_path)


@app.errorhandler(413)
def too_large(_e):
    return jsonify(error="Image too large. Max size is 10MB."), 413


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
