from flask import Flask, request, jsonify, render_template
import os
import docx
import pdfplumber  # Improved PDF text extraction
import re
from werkzeug.utils import secure_filename
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Function to extract text from DOCX
def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = '\n'.join([para.text for para in doc.paragraphs])
    return text.strip()

# Improved function to extract text from PDF
def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

# Function to preprocess text (normalize case, remove extra spaces)
def preprocess_text(text):
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces and newlines
    return text.strip()

# Jaccard Similarity function
def jaccard_similarity(text1, text2):
    set1, set2 = set(text1.split()), set(text2.split())
    return len(set1 & set2) / len(set1 | set2) if len(set1 | set2) > 0 else 0

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No files uploaded"}), 400

    files = request.files.getlist('files')
    stored_texts = []
    
    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Extract text based on file type
        if filename.endswith('.docx'):
            text = extract_text_from_docx(file_path)
        elif filename.endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        else:
            text = "Unsupported file format"
        
        text = preprocess_text(text)  # Normalize the text before comparison
        stored_texts.append((filename, text))

        # Debugging: Print extracted text in console
        print(f"\nExtracted Text from {filename}:\n{text}\n{'='*50}")

    # Perform plagiarism check
    plagiarism_results = []
    for i, (file1, text1) in enumerate(stored_texts):
        for j, (file2, text2) in enumerate(stored_texts):
            if i >= j:  # Avoid duplicate checks
                continue
            
            # Compute Cosine Similarity
            vectorizer = TfidfVectorizer().fit_transform([text1, text2])
            cosine_sim = cosine_similarity(vectorizer)[0][1]
            
            # Compute Jaccard Similarity
            jaccard_sim = jaccard_similarity(text1, text2)
            
            plagiarism_results.append({
                "file1": file1,
                "file2": file2,
                "cosine_similarity": round(cosine_sim * 100, 2),
                "jaccard_similarity": round(jaccard_sim * 100, 2)
            })
    
    return jsonify({"plagiarism_results": plagiarism_results})

if __name__ == '__main__':
    app.run(debug=True)
