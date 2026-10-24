"""SQLite storage for analysis results (resume text is NOT stored, for privacy)."""
import json
import os
import sqlite3
import uuid
from datetime import datetime

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "analyses.db"))


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT, role TEXT, resume_score INTEGER, ats_score REAL,
            result_json TEXT, created_at TEXT)""")
        try:  # upgrade older databases that have no token column
            c.execute("ALTER TABLE analyses ADD COLUMN token TEXT")
        except sqlite3.OperationalError:
            pass


def save_analysis(filename, role, resume_score, ats_score, result):
    token = uuid.uuid4().hex
    with _conn() as c:
        c.execute(
            "INSERT INTO analyses (filename, role, resume_score, ats_score, result_json, created_at, token) VALUES (?,?,?,?,?,?,?)",
            (filename, role, resume_score, ats_score, json.dumps(result), datetime.now().strftime("%d %b %Y, %H:%M"), token))
    return token


def get_analysis(token):
    with _conn() as c:
        row = c.execute("SELECT * FROM analyses WHERE token=?", (token,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["result"] = json.loads(d.pop("result_json"))
    return d


def list_analyses(tokens, limit=20):
    """Only the analyses whose tokens belong to this visitor's session."""
    if not tokens:
        return []
    marks = ",".join("?" * len(tokens))
    with _conn() as c:
        rows = c.execute(
            f"SELECT token, filename, role, resume_score, ats_score, created_at FROM analyses WHERE token IN ({marks}) ORDER BY id DESC LIMIT ?",
            (*tokens, limit)).fetchall()
    return [dict(r) for r in rows]
