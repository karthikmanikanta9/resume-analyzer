# Smart Resume Analyzer with AI-Based Feedback

An AI-powered web app that analyzes a student's resume and gives a **resume score (0-100)**, an **ATS compatibility score** for a chosen job role, a **skill gap** list and **prioritised improvement suggestions** on an interactive dashboard.

Built for the SkillOrbit AI Capstone (Aug 2026 batch).

**Live demo:**  https://smart-resume-analyzer-yr1i.onrender.com  

## Features
- Upload resumes in **PDF or DOCX** (max 5 MB) with friendly error handling
- **Role-aware resume score out of 100** with a per-section breakdown (contact, education, skills, projects, experience, certifications, structure)
- **ATS keyword checker** for 4 roles: Data Analyst, Web Developer, AI Engineer, Cloud Engineer
- **TF-IDF cosine similarity** as a second NLP-based ATS signal
- **Smart feedback** ranked High / Medium / Low
- **Dashboard** with gauges, charts, matched/missing skills and a printable report
- **History** page backed by SQLite (each visitor sees only their own analyses)
- Privacy: uploaded files are deleted right after text extraction; resume text is never stored

## How the AI logic works
| Part | Method |
|---|---|
| Section detection | Regex on short, heading-like lines |
| Resume score | Weighted rule-based rubric (total 100) |
| Keyword match | Word-boundary matching against `roles.json` (with aliases) |
| Similarity | TF-IDF vectors + cosine similarity (scikit-learn) |
| **ATS score** | `0.7 x keyword match % + 0.3 x similarity %` |
| Feedback | If-then rules over the score and missing keywords |

Score rubric: Contact 15, Education 15, Skills 20, Projects 20, Experience 10, Certifications 10, Structure and length 10.

## Tech stack
Python Flask, pdfplumber, python-docx, scikit-learn, SQLite, Bootstrap 5, Chart.js, Gunicorn, deployed on Render.

## Project structure
```
app.py            Flask routes
resume_parser.py  Module 1: PDF/DOCX text extraction
scorer.py         Module 2: resume score
ats.py            Module 3: ATS keyword match + TF-IDF
feedback.py       Module 4: suggestions
db.py             SQLite storage
roles.json        Keywords per role (edit to add roles)
templates/        HTML pages
static/           CSS
test_modules.py   Command-line test script
```

## Run locally
```bash
git clone https://github.com/[YOUR-USERNAME]/resume-analyzer.git
cd resume-analyzer
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

Test the logic without the web app:
```bash
python test_modules.py path/to/resume.pdf
```

## Deploy on Render
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Environment variables: `PYTHON_VERSION=3.11.9`, `SECRET_KEY=<any random text>`

## Test results
| Resume | Score |
|---|---|
| Strong sample | 94 / 100 |
| Medium sample | 84 / 100 |
| Weak sample | 44 / 100 |

## Limitations and future scope
- No OCR for scanned resumes
- Keyword lists cover 4 roles (extend `roles.json`)
- Free-tier hosting resets saved history on restart
- Future: job-description matching, BERT embeddings, user accounts

## Author
Karthik Manikanta Neyyala, CSE (AI and ML), SkillOrbit Aug 2026 batch
