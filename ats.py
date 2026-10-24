"""Module 3: ATS keyword checker + TF-IDF similarity."""
import json
import os
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "roles.json"), encoding="utf-8") as f:
    ROLES = json.load(f)


def list_roles():
    return list(ROLES.keys())


def _present(alias, text):
    # whole-token match that also works for c++, node.js, ci/cd
    pattern = r"(?<![a-z0-9])" + re.escape(alias.strip()) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def keyword_match(text, role):
    low = text.lower()
    matched, missing = [], []
    for entry in ROLES[role]:
        aliases = entry.split("|")
        label = aliases[0]
        (matched if any(_present(a, low) for a in aliases) else missing).append(label)
    pct = round(100 * len(matched) / len(ROLES[role]), 1)
    return matched, missing, pct


def tfidf_similarity(text, role):
    """Cosine similarity between resume and the role's keyword profile (0-100)."""
    profile = " ".join(e.split("|")[0] for e in ROLES[role])
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        m = vec.fit_transform([text.lower(), profile])
        sim = float(cosine_similarity(m[0], m[1])[0][0])
    except ValueError:
        return 0.0
    # raw cosine for short keyword profiles is small, so scale and cap at 100
    return round(min(sim * 4, 1.0) * 100, 1)


def ats_analysis(text, role):
    if role not in ROLES:
        raise ValueError("Unknown role")
    matched, missing, kw_pct = keyword_match(text, role)
    sim = tfidf_similarity(text, role)
    score = round(0.7 * kw_pct + 0.3 * sim, 1)
    return {"role": role, "ats_score": score, "keyword_match_pct": kw_pct,
            "similarity_pct": sim, "matched": matched, "missing": missing}
