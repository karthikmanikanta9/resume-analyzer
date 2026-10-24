"""Module 2: Rule-based resume scoring (0-100)."""
import re

from ats import ROLES

# section name -> heading words that identify it
SECTION_PATTERNS = {
    "contact": r"contact|personal (details|information)",
    "summary": r"summary|objective|profile|about me",
    "education": r"education|academic|qualification",
    "skills": r"skills|technical skills|technologies|tools|competenc",
    "projects": r"projects?|academic projects|personal projects",
    "experience": r"experience|internships?|work history|employment",
    "certifications": r"certifications?|certificates?|courses|licen[cs]es|achievements|awards",
}

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(\+?\d{1,3}[\s-]?)?(\(?\d{3,5}\)?[\s-]?)?\d{3,5}[\s-]?\d{4,5}")
LINKS = re.compile(r"linkedin\.com|github\.com|portfolio|gitlab\.com", re.I)
YEAR = re.compile(r"\b(19|20)\d{2}\b")
DEGREE = re.compile(r"b\.?\s?tech|b\.?\s?e\b|b\.?\s?sc|bca|mca|m\.?\s?tech|m\.?\s?sc|mba|bachelor|master|diploma|b\.?com|12th|intermediate|university|college|institute|school", re.I)
ACTION_VERBS = re.compile(r"\b(built|developed|designed|implemented|created|analyzed|analysed|deployed|automated|optimized|optimised|led|managed|engineered|trained|integrated)\b", re.I)


def _is_heading_line(raw):
    """A heading is a short line with only letters/spaces/&/ (no commas, colons, dots, pipes, digits)."""
    raw = raw.strip().lstrip("#* ").rstrip("* ")
    return bool(raw) and len(raw.split()) <= 5 and re.fullmatch(r"[A-Za-z &/]+", raw) is not None


def detect_sections(text):
    """Find which sections exist by looking for heading-like short lines."""
    found = {}
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for idx, line in enumerate(lines):
        if not _is_heading_line(line):
            continue
        clean = line.strip().lstrip("#* ").rstrip("* ")
        for name, pat in SECTION_PATTERNS.items():
            if name in found:
                continue
            # exact heading ("Skills") or heading starting with a keyword ("Certifications & Activities")
            if re.fullmatch(rf"(?i)({pat})s?", clean) or re.match(rf"(?i)^({pat})s?\b", clean) \
                    or re.search(rf"(?i)\b({pat})s?$", clean):
                found[name] = idx
                break
    return found, lines


def section_text(lines, found, name):
    """Return the text under a heading until the next heading."""
    if name not in found:
        return ""
    start = found[name] + 1
    later = [i for i in found.values() if i > found[name]]
    end = min(later) if later else len(lines)
    return "\n".join(lines[start:end])


KNOWN_SKILLS = sorted({a.strip() for lst in ROLES.values() for e in lst for a in e.split("|") if len(a.strip()) > 1})


def _count_skills(block):
    low = block.lower()
    return sum(1 for k in KNOWN_SKILLS
               if re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", low))


def _substantive(block, min_len=60):
    return len([l for l in block.split("\n") if len(l.strip()) >= min_len])


def _count_items(block):
    return len([l for l in block.split("\n") if len(l.strip()) > 15])


def score_resume(text):
    found, lines = detect_sections(text)
    sec = lambda n: section_text(lines, found, n)
    breakdown, notes = {}, {}

    # Contact (15)
    pts = 0
    has_email = bool(EMAIL.search(text))
    has_phone = bool(PHONE.search(text[:600]))
    has_link = bool(LINKS.search(text))
    pts += 5 if has_email else 0
    pts += 5 if has_phone else 0
    pts += 5 if has_link else 0
    breakdown["Contact Info"] = (pts, 15)
    notes["Contact Info"] = {"email": has_email, "phone": has_phone, "linkedin/github": has_link}

    # Education (15)
    edu = sec("education")
    pts = 0
    if "education" in found:
        pts += 5
    if DEGREE.search(edu or text):
        pts += 5
    if YEAR.search(edu or text):
        pts += 5
    breakdown["Education"] = (pts, 15)

    # Skills (20): heading 4 + number of recognised technical skills (16)
    skills = sec("skills")
    pts = 0
    if "skills" in found:
        pts += 4
        n = _count_skills(skills)
        pts += 16 if n >= 10 else (12 if n >= 6 else (8 if n >= 3 else (4 if n >= 1 else 0)))
    breakdown["Skills"] = (pts, 20)

    # Projects (20): heading 4 + substantive entries 6 + action verbs 5 + tech keywords 5
    proj = sec("projects")
    pts = 0
    if "projects" in found:
        pts += 4
        items = _substantive(proj)
        pts += 6 if items >= 3 else (3 if items >= 1 else 0)
        verbs = len(ACTION_VERBS.findall(proj))
        pts += 5 if verbs >= 3 else (2 if verbs >= 1 else 0)
        tech = _count_skills(proj)
        pts += 5 if tech >= 3 else (2 if tech >= 1 else 0)
    breakdown["Projects"] = (pts, 20)

    # Experience (10): heading 3 + role/dates 3 + a substantive description 4
    exp = sec("experience")
    pts = 0
    if "experience" in found:
        pts += 3
        if YEAR.search(exp) or re.search(r"\b(intern|trainee|developer|analyst|engineer|contributor)\b", exp, re.I):
            pts += 3
        pts += 4 if _substantive(exp, 40) >= 1 else 0
    breakdown["Experience"] = (pts, 10)

    # Certifications (10)
    cert = sec("certifications")
    pts = 0
    if "certifications" in found:
        pts += 5
        pts += 5 if _count_items(cert) >= 1 else 0
    breakdown["Certifications"] = (pts, 10)

    # Structure & length (10)
    words = len(text.split())
    pts = 0
    pts += 5 if len(found) >= 4 else (2 if len(found) >= 3 else 0)
    pts += 5 if 250 <= words <= 900 else (2 if 150 <= words < 250 or 900 < words <= 1200 else 0)
    breakdown["Structure & Length"] = (pts, 10)
    notes["Structure & Length"] = {"words": words, "sections_found": sorted(found.keys())}

    total = sum(p for p, _ in breakdown.values())
    return {"total": total, "breakdown": breakdown, "notes": notes,
            "sections_found": sorted(found.keys()), "word_count": words}
