"""SQLite storage for analysis results (resume text is NOT stored, for privacy)."""
import json
import os
import sqlite3
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


def save_analysis(filename, role, resume_score, ats_score, result):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO analyses (filename, role, resume_score, ats_score, result_json, created_at) VALUES (?,?,?,?,?,?)",
            (filename, role, resume_score, ats_score, json.dumps(result), datetime.now().strftime("%d %b %Y, %H:%M")))
        return cur.lastrowid


def get_analysis(analysis_id):
    with _conn() as c:
        row = c.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["result"] = json.loads(d.pop("result_json"))
    return d


def list_analyses(limit=20):
    with _conn() as c:
        rows = c.execute("SELECT id, filename, role, resume_score, ats_score, created_at FROM analyses ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
