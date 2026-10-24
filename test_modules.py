import sys, glob
from resume_parser import extract_text
from scorer import score_resume
from ats import ats_analysis, list_roles

files = sys.argv[1:] or glob.glob("samples/*")
for f in files:
    print("=" * 60, "\nFILE:", f)
    try:
        text = extract_text(f)
    except ValueError as e:
        print("ERROR:", e); continue
    r = score_resume(text, "Data Analyst")
    print("Resume score:", r["total"], "/ 100")
    for k, (p, m) in r["breakdown"].items():
        print(f"   {k:20s} {p}/{m}")
    print("Sections found:", r["sections_found"])
    for role in list_roles():
        a = ats_analysis(text, role)
        print(f"ATS {role:15s} {a['ats_score']:5} (kw {a['keyword_match_pct']}%, sim {a['similarity_pct']}%)")
    a = ats_analysis(text, "Data Analyst")
    print("Data Analyst matched:", a["matched"]); print("Data Analyst missing:", a["missing"][:8])
