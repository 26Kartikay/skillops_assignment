from flask import Flask, request, jsonify, render_template
import fitz
from docx import Document
import pandas as pd
import os
import re

app = Flask(__name__)

hard_skills_file_path = "Hard_skills.xlsx"
soft_skills_file_path = "soft_skills.xlsx"

def extract_text_from_pdf(path):
    try:
        doc = fitz.open(path)
        return " ".join([page.get_text() for page in doc])
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def extract_text_from_docx(path):
    try:
        doc = Document(path)
        return " ".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""

def load_skills_from_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        return df["Text"].dropna().astype(str).str.lower().str.strip().tolist()
    except Exception as e:
        print(f"Error loading skills from Excel: {e}")
        return []

def extract_skills(text, skill_list):
    text = text.lower()
    return sorted([skill for skill in skill_list if re.search(r'\b' + re.escape(skill) + r'\b', text)])

def get_resume_skills(resume_path, hard_skills_file, soft_skills_file):
    hard_skills = load_skills_from_excel(hard_skills_file)
    soft_skills = load_skills_from_excel(soft_skills_file)
    ext = os.path.splitext(resume_path)[-1].lower()
    if ext == '.pdf':
        text = extract_text_from_pdf(resume_path)
    elif ext == '.docx':
        text = extract_text_from_docx(resume_path)
    else:
        raise ValueError("Unsupported file type. Use PDF or DOCX.")
    matched_hard_skills = extract_skills(text, hard_skills)
    matched_soft_skills = extract_skills(text, soft_skills)
    return matched_hard_skills, matched_soft_skills

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file provided"}), 400

    resume = request.files['resume']
    if resume.filename == '':
        return jsonify({"error": "No selected file"}), 400

    resume_path = os.path.join("uploads", resume.filename)
    os.makedirs(os.path.dirname(resume_path), exist_ok=True)
    resume.save(resume_path)

    if not os.path.exists(hard_skills_file_path) or not os.path.exists(soft_skills_file_path):
        return jsonify({"error": "Skill Excel files not found"}), 400

    hard_skills_found, soft_skills_found = get_resume_skills(resume_path, hard_skills_file_path, soft_skills_file_path)
    filtered_hard_skills = [skill for skill in hard_skills_found if len(skill) >= 5]
    filtered_soft_skills = [skill for skill in soft_skills_found if len(skill) >= 5]

    top_hard_skills = filtered_hard_skills[:10]
    top_soft_skills = filtered_soft_skills[:10]

    skills_data = [
        {"Skill Category": "Soft Skills", "Skills": [skill.capitalize() for skill in top_soft_skills]},
        {"Skill Category": "Technical Skills", "Skills": [skill.capitalize() for skill in top_hard_skills]}
    ]

    return jsonify(skills_data)

if __name__ == "__main__":
    app.run(debug=True)
