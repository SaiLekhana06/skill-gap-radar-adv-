import streamlit as st
import pandas as pd
import re
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

resume_skills = []

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="Skill Gap Radar", layout="wide")

# -----------------------------
# Load Dataset
# -----------------------------
@st.cache_data
def load_data():
    file = "Skill_Gap_Radar_dataset(1).xlsx"
    jobs = pd.read_excel(file, sheet_name="job_description_enriched")
    fields = pd.read_excel(file, sheet_name="field_intelligence")
    resources = pd.read_excel(file, sheet_name="skill_learning_resources")
    return jobs, fields, resources

df_jobs, df_fields, df_resources = load_data()

# -----------------------------
# Resume Text Extraction
# -----------------------------
def extract_text(file):
    text = ""

    if file.type == "application/pdf":
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + " "

    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(file)
        for para in doc.paragraphs:
            text += para.text + " "

    elif file.type.startswith("image"):
        image = Image.open(file)
        text = pytesseract.image_to_string(image)

    return text.lower()

# -----------------------------
# Skill Matching
# -----------------------------
def match_skills(resume_text, required_skills):
    matched = []
    for skill in required_skills:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, resume_text):
            matched.append(skill)
    missing = list(set(required_skills) - set(matched))
    return matched, missing

# -----------------------------
# Resume Skill Extraction
# -----------------------------
def extract_resume_skills(resume_text):
    skills_found = []
    all_skills = set()

    for skills in df_jobs["skills_required"]:
        for skill in skills.split(","):
            all_skills.add(skill.strip().lower())

    for skill in all_skills:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, resume_text):
            skills_found.append(skill)

    return list(set(skills_found))

# -----------------------------
# Weighted Scoring Formula
# -----------------------------
def calculate_score(matched, required, demand, future, competition):
    if len(required) == 0:
        return 0

    skill_match = len(matched) / len(required)
    score = (
        (skill_match * 0.6)
        + (demand / 10 * 0.2)
        + (future / 10 * 0.1)
        - (competition / 10 * 0.1)
    )
    return round(score * 100, 2)

# -----------------------------
# Sidebar Navigation
# -----------------------------
st.sidebar.title("Skill Gap Radar 🚀")
page = st.sidebar.radio("Navigate", ["Block 1: Target Job Analyzer",
                                      "Block 2: Market Intelligence",
                                      "Block 3: Resume Role Finder"])

# ==============================================================
# BLOCK 1
# ==============================================================
if page == "Block 1: Target Job Analyzer":

    st.title("🎯 Target Job Analyzer")

    field = st.selectbox("Select Field", sorted(df_jobs["field_name"].unique()))
    filtered_jobs = df_jobs[df_jobs["field_name"] == field]

    job_title = st.selectbox("Select Job Title", sorted(filtered_jobs["job_title"].unique()))
    selected_job = filtered_jobs[filtered_jobs["job_title"] == job_title].iloc[0]

    # ✅ Added image formats here
    uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "jpg", "jpeg", "png"])

    if uploaded_file:
        resume_text = extract_text(uploaded_file)

        required_skills = [s.strip().lower() for s in selected_job["skills_required"].split(",")]
        matched, missing = match_skills(resume_text, required_skills)

        score = calculate_score(
            matched,
            required_skills,
            selected_job["demand_score"],
            selected_job["growth_rate_percent"],
            selected_job["competition_index"],
        )

        st.subheader("📊 Readiness Score")
        st.progress(int(score))
        st.write(f"### {score}% Match for {job_title}")

        st.subheader("✅ Matched Skills")
        st.write(matched if matched else "No skills matched")

        st.subheader("❌ Missing Skills")
        st.write(missing if missing else "None")

        if missing:
            st.subheader("📚 Recommended Learning Path")

            for skill in missing:
                rec = df_resources[df_resources["skill"].str.lower() == skill.lower()]

                if not rec.empty:
                    course_name = rec.iloc[0]["recommended_course"]
                    course_url = rec.iloc[0]["course_url"]

                    cert_name = rec.iloc[0]["certification"]
                    cert_url = rec.iloc[0]["certification_url"]

                    project = rec.iloc[0]["project_suggestion"]

                    st.markdown(f"### 🔹 Skill: **{skill}**")

            # Course hyperlink
                    st.markdown(f"📘 **Course:** [{course_name}]({course_url})")

            # Certification hyperlink
                    st.markdown(f"🎓 **Certification:** [{cert_name}]({cert_url})")

            # Project (text only)
                    st.markdown(f"🛠 **Project:** {project}")

                    st.markdown("---")

# ==============================================================
# BLOCK 2
# ==============================================================
elif page == "Block 2: Market Intelligence":

    st.title("📈 Market Intelligence Dashboard")

    field = st.selectbox("Select Field", sorted(df_jobs["field_name"].unique()))
    filtered_jobs = df_jobs[df_jobs["field_name"] == field]

    st.subheader("Average Salary by Role")
    st.bar_chart(filtered_jobs.set_index("job_title")["avg_salary_lpa"])

    st.subheader("AI Risk by Role")
    st.bar_chart(filtered_jobs.set_index("job_title")["ai_risk_score"])

    st.subheader("Growth Rate by Role")
    st.bar_chart(filtered_jobs.set_index("job_title")["growth_rate_percent"])

# ==============================================================
# BLOCK 3
# ==============================================================
elif page == "Block 3: Resume Role Finder":

    st.title("🧠 Resume → Top 3 Suitable Roles")

    uploaded_file = st.file_uploader(
        "Upload Resume",
        type=["pdf", "docx", "jpg", "jpeg", "png"]
    )

    if uploaded_file:
        resume_text = extract_text(uploaded_file)
        resume_skills = extract_resume_skills(resume_text)

        role_scores = []

        for _, row in df_jobs.iterrows():
            role = row["job_title"]
            required_skills = [s.strip().lower() for s in row["skills_required"].split(",")]

            matched = set(resume_skills).intersection(required_skills)
            missing = list(set(required_skills) - matched)

            skill_match_ratio = len(matched) / len(required_skills) if required_skills else 0

            score = (
                (skill_match_ratio * 0.6)
                + (row["demand_score"] / 10 * 0.2)
                + (row["growth_rate_percent"] / 10 * 0.1)
                - (row["competition_index"] / 10 * 0.1)
            ) * 100

            role_scores.append({
                "role": role,
                "score": round(score, 2),
                "missing_skills": missing,
                "ai_risk": row["ai_risk_score"],
                "competition": row["competition_index"],
                "salary": row["avg_salary_lpa"]
            })

        top_roles = sorted(role_scores, key=lambda x: x["score"], reverse=True)[:3]

        st.subheader("🏆 Top 3 Suitable Roles")

        for r in top_roles:
            st.markdown(f"## 🧑‍💼 {r['role']}")
            st.write(f"**Readiness Score:** {r['score']}%")
            st.write(f"**Average Salary:** {r['salary']} LPA")
            st.write(f"**AI Risk Score:** {r['ai_risk']}/10")
            st.write(f"**Competition Index:** {r['competition']}/10")

            if r["missing_skills"]:
                st.warning("Skill Gap Detected")
                st.write("### 📚 Recommended Skills to Learn")

                for skill in r["missing_skills"]:
                    rec = df_resources[df_resources["skill"].str.lower() == skill.lower()]

                    st.markdown(f"**🔹 {skill}**")

                    if not rec.empty:
                        course_name = rec.iloc[0]["recommended_course"]
                        course_url = rec.iloc[0]["course_url"]

                        cert_name = rec.iloc[0]["certification"]
                        cert_url = rec.iloc[0]["certification_url"]

                        st.markdown(f"📘 Course: [{course_name}]({course_url})")
                        st.markdown(f"🎓 Certification: [{cert_name}]({cert_url})")
                    else:
                        st.write("No learning resources found.")

                    st.markdown("---")

            st.divider()