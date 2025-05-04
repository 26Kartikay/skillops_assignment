from flask import Flask, request, render_template
import os
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import fitz

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def preprocess_text(text):
    doc = nlp(text.lower())
    tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    return " ".join(tokens)

def match_resumes_to_job(resume_texts, job_description):
    all_docs = resume_texts + [job_description]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_docs)
    job_vector = tfidf_matrix[-1]
    resume_vectors = tfidf_matrix[:-1]
    scores = cosine_similarity(resume_vectors, job_vector)
    return scores.flatten()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('resumes')
        job_description = request.form['job']
        resume_texts = []
        candidate_names = []
        for file in files:
            if file and file.filename.endswith('.pdf'):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                text = extract_text_from_pdf(filepath)
                resume_texts.append(preprocess_text(text))
                candidate_names.append(file.filename)
        job_desc_processed = preprocess_text(job_description)
        scores = match_resumes_to_job(resume_texts, job_desc_processed)
        matched = list(zip(candidate_names, scores))
        matched.sort(key=lambda x: x[1], reverse=True)
        return render_template('template1/result.html', matched=matched)
    return render_template('template1/index.html')

if __name__ == '__main__':
    app.run(debug=True)
