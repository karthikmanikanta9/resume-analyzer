"""Module 4: Smart feedback - turns score + ATS results into prioritised suggestions."""
import re

# per-skill advice used when a high-value keyword is missing for the chosen role
SKILL_TIPS = {
    "sql": "Add SQL: list databases you used (MySQL/PostgreSQL) and queries you wrote in a project.",
    "excel": "Mention Excel (pivot tables, formulas, charts) with one example of what you analysed.",
    "power bi": "Add Power BI or Tableau dashboards to a project and describe the insight you showed.",
    "tableau": "Add Tableau or Power BI dashboards to a project and describe the insight you showed.",
    "python": "List Python clearly in Skills and show it inside at least one project.",
    "react": "Include React projects (components, hooks, API calls) and link the GitHub repo.",
    "git": "Mention Git/GitHub and add your repository links to each project.",
    "javascript": "Add JavaScript skills and a project that uses it (DOM, fetch/API, ES6).",
    "rest api": "Mention REST APIs you built or consumed (Flask/Express) in a project.",
    "aws": "Mention cloud technologies: AWS services you used (EC2, S3, IAM, Lambda).",
    "azure": "Mention Azure fundamentals or services you worked with.",
    "docker": "Add Docker: containerize one of your projects and say so in the project bullet.",
    "kubernetes": "Add Kubernetes basics (pods, deployments) if you have practised them.",
    "linux": "Mention Linux and shell commands/scripting you are comfortable with.",
    "ci/cd": "Add CI/CD (GitHub Actions or Jenkins) to a project to show automation skills.",
    "machine learning": "Add machine learning projects with models, metrics (accuracy, F1) and datasets used.",
    "deep learning": "Include a deep learning project (CNN/RNN/LSTM) with TensorFlow or PyTorch.",
    "tensorflow": "Mention TensorFlow/Keras or PyTorch with the model you trained.",
    "pytorch": "Mention PyTorch or TensorFlow with the model you trained.",
    "nlp": "Add an NLP project (text classification, sentiment, BERT/transformers).",
    "pandas": "Mention pandas and NumPy for data handling in your skills and projects.",
    "statistics": "Mention statistics concepts you applied (regression, hypothesis testing).",
}

ROLE_CERTS = {
    "Data Analyst": "Google Data Analytics Certificate or Microsoft Power BI (PL-300)",
    "Web Developer": "freeCodeCamp Responsive Web Design / JavaScript certification",
    "AI Engineer": "DeepLearning.AI / Coursera Machine Learning or TensorFlow Developer certificate",
    "Cloud Engineer": "AWS Cloud Practitioner or Azure Fundamentals (AZ-900)",
}

PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def generate_feedback(text, score_result, ats_result):
    tips = []
    add = lambda p, t: tips.append({"priority": p, "text": t})
    b = {k: v[0] for k, v in score_result["breakdown"].items()}
    notes = score_result["notes"]["Contact Info"]
    role = ats_result["role"]

    # --- contact ---
    if not notes["email"]:
        add("High", "Add a professional email address at the top of your resume.")
    if not notes["phone"]:
        add("High", "Add your phone number in the header so recruiters can reach you.")
    if not notes["linkedin/github"]:
        add("Medium", "Add your LinkedIn and GitHub links; recruiters check them for projects.")

    # --- sections ---
    if b["Projects"] < 14:
        add("High", "Add 2-3 technical projects. For each one: what you built, the tools used, and the result.")
    if b["Skills"] < 14:
        add("High", f"Strengthen the Skills section with tools relevant to a {role} (see missing keywords).")
    if b["Education"] < 15:
        add("Medium", "Complete the Education section: degree, institution and years (with CGPA if good).")
    if b["Experience"] < 6:
        add("Medium", "Add internship or practical experience, or list team/academic work with your role and dates.")
    if b["Certifications"] < 10:
        add("Medium", f"Include certifications, for example: {ROLE_CERTS[role]}.")

    # --- structure ---
    words = score_result["word_count"]
    if words < 250:
        add("Medium", "Your resume is too short. Expand project and skill descriptions to about 300-700 words.")
    elif words > 900:
        add("Low", "Your resume is long. Trim it to 1-2 pages and keep only relevant content.")
    if len(score_result["sections_found"]) < 4:
        add("High", "Improve resume formatting: use standard headings (Education, Skills, Projects, Experience, Certifications).")
    if not re.search(r"\d+\s?%|\b\d{2,}\+?\b|\$\s?\d", text):
        add("Low", "Quantify your work with numbers (e.g. 'analysed 50k records', 'improved accuracy to 86%').")
    if score_result["notes"] and "summary" not in score_result["sections_found"]:
        add("Low", "Add a 2-3 line professional summary tailored to your target role.")

    # --- ATS keywords ---
    missing = ats_result["missing"]
    kw = ats_result["keyword_match_pct"]
    if kw < 40:
        add("High", f"Low ATS match for {role} ({kw}%). Add the missing keywords wherever you truly have the skill.")
    elif kw < 70:
        add("Medium", f"Good start for {role} ({kw}% match). Add a few more of the missing keywords.")
    given = 0
    for m in missing:
        if m in SKILL_TIPS and given < 4:
            add("High" if given < 2 else "Medium", SKILL_TIPS[m])
            given += 1
    if missing and given == 0:
        add("Medium", "Consider adding: " + ", ".join(missing[:6]) + ".")

    if not tips:
        add("Low", "Excellent resume! Keep it updated and tailor the keywords to each job description.")

    # de-duplicate, then sort by priority
    seen, unique = set(), []
    for t in tips:
        if t["text"] not in seen:
            seen.add(t["text"]); unique.append(t)
    unique.sort(key=lambda t: PRIORITY_ORDER[t["priority"]])
    return unique
