"""Smart Resume Analyzer - Flask app (Modules 1-5 wired together)."""
import os
import tempfile
import uuid

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

import db
from ats import ats_analysis, list_roles
from feedback import generate_feedback
from resume_parser import allowed_file, extract_text
from scorer import score_resume

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB
db.init_db()


def grade(score):
    if score >= 80:
        return "Excellent", "success"
    if score >= 60:
        return "Good", "primary"
    if score >= 40:
        return "Needs Work", "warning"
    return "Weak", "danger"


@app.route("/")
def index():
    return render_template("index.html", roles=list_roles())


@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("resume")
    role = request.form.get("role", "")
    if not file or file.filename == "":
        flash("Please choose a resume file (PDF or DOCX).", "danger")
        return redirect(url_for("index"))
    if not allowed_file(file.filename):
        flash("Unsupported file type. Please upload a PDF or DOCX.", "danger")
        return redirect(url_for("index"))
    if role not in list_roles():
        flash("Please select a target job role.", "danger")
        return redirect(url_for("index"))

    ext = file.filename.rsplit(".", 1)[1].lower()
    tmp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.{ext}")
    file.save(tmp_path)
    try:
        text = extract_text(tmp_path)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("index"))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)  # privacy: delete the uploaded file immediately

    score = score_resume(text, role)
    ats = ats_analysis(text, role)
    all_roles = {r: ats_analysis(text, r)["ats_score"] for r in list_roles()}
    all_scores = {r: score_resume(text, r)["total"] for r in list_roles()}
    tips = generate_feedback(text, score, ats)

    result = {
        "score": score["total"],
        "breakdown": {k: {"got": v[0], "max": v[1]} for k, v in score["breakdown"].items()},
        "sections_found": score["sections_found"],
        "word_count": score["word_count"],
        "ats": ats,
        "all_roles": all_roles,
        "all_scores": all_scores,
        "tips": tips,
    }
    token = db.save_analysis(secure_filename(file.filename), role, score["total"], ats["ats_score"], result)
    session["tokens"] = (session.get("tokens", []) + [token])[-30:]
    return redirect(url_for("dashboard", token=token))


@app.route("/result/<token>")
def dashboard(token):
    rec = db.get_analysis(token)
    if not rec:
        flash("Analysis not found.", "danger")
        return redirect(url_for("index"))
    label, color = grade(rec["result"]["score"])
    return render_template("dashboard.html", rec=rec, r=rec["result"], label=label, color=color)


@app.route("/history")
def history():
    return render_template("history.html", items=db.list_analyses(session.get("tokens", [])))


@app.errorhandler(413)
def too_large(_):
    flash("File too large. Maximum size is 5 MB.", "danger")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
