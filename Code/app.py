import os
import re
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import time
from datetime import datetime
import traceback
import re
import tempfile
import pdfplumber
import pytesseract
from pdf2image import convert_from_path

from Code.base.scraping import get_pdf_text, extract_claims
from Code.base.patent_logic import analyze_claims

app = Flask(__name__, template_folder = 'ui/templates')

# Get the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Folder where uploaded files are stored
UPLOAD_FOLDER      = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    """Render the homepage."""
    return render_template('index.html')

@app.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """Enhanced clause analysis endpoint with improved parsing and features"""
    try:
        # Input validation
        patent_file = request.files.get('patent')
        if not patent_file:
            return jsonify({"error": "No file uploaded"}), 400

        # File handling
        upload_path = os.path.join("uploads", patent_file.filename)
        patent_file.save(upload_path)

        # Extract text and claims
        patent_text = get_pdf_text(upload_path)
        claims = extract_claims(patent_text)
        print('we got claims')

        # Enhanced analysis pipeline
        analysis_start = time.time()
        print('starting analysis...')

        # ✅ masked secrets: pull from environment (no hard-coded key)
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"error": "Missing OPENAI_API_KEY environment variable"}), 500

        api_base = os.environ.get("OPENAI_API_BASE", "https://api.sambanova.ai/v1")

        final_evaluation = analyze_claims(
            claims_text = claims,
            model         = 'Meta-Llama-3.3-70B-Instruct',
            role          = "user",
            api_key       = api_key,
            api_base      = api_base,
            temperature   = 0.1,
            top_p         = 1.0,
            max_tokens    = 4096
        )

        print(f"Analysis completed in {time.time() - analysis_start:.2f}s")
        return jsonify(final_evaluation)

    except Exception as e:
        app.logger.error(f"Analysis error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Analysis failed",
            "message": str(e),
            "trace": traceback.format_exc() if app.debug else None
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
