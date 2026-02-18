import streamlit as st
import pandas as pd
import re
import pdfplumber
from docx import Document

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
    if file.name.endswith(".pdf"):
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + " "
        return text.lower()
    elif file.name.endswith(".docx"):
        doc = Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + " "
        return text.lower()
    return ""

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

    uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])

    if uploaded_file:
        resume_text = extract_text(uploaded_file)

        required_skills = [s.strip() for s in selected_job["skills_required"].split(",")]

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
            st.subheader("📚 Recommended Certifications & Projects")
            for skill in missing:
                rec = df_resources[df_resources["skill"] == skill]
                if not rec.empty:
                    st.markdown(f"**Skill:** {skill}")
                    st.write("Course:", rec.iloc[0]["recommended_course"])
                    st.write("Certification:", rec.iloc[0]["certification"])
                    st.write("Project:", rec.iloc[0]["project_suggestion"])
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

    uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])

    if uploaded_file:
        resume_text = extract_text(uploaded_file)

        role_scores = []

        for _, row in df_jobs.iterrows():
            required_skills = [s.strip() for s in row["skills_required"].split(",")]
            matched, _ = match_skills(resume_text, required_skills)

            score = calculate_score(
                matched,
                required_skills,
                row["demand_score"],
                row["growth_rate_percent"],
                row["competition_index"],
            )

            role_scores.append((row["job_title"], score))

        role_scores = sorted(role_scores, key=lambda x: x[1], reverse=True)[:3]

        st.subheader("🏆 Top 3 Suitable Roles")

        for title, score in role_scores:
            st.markdown(f"### {title}")
            st.write(f"Match Score: {score}%")
            st.markdown("---")
