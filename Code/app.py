import os
import time
import tempfile
from flask import Flask, render_template, request, jsonify

from Code.base.scraping import get_pdf_text, extract_claims
from Code.base.patent_logic import analyze_claims

app = Flask(__name__, template_folder = 'ui/templates')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    patent_file = request.files.get('patent')
    if not patent_file:
        return jsonify({"error": "No file uploaded"}), 400

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "Missing OPENAI_API_KEY environment variable"}), 500

    api_base = os.environ.get("OPENAI_API_BASE", "https://api.sambanova.ai/v1")

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    try:
        os.close(tmp_fd)
        patent_file.save(tmp_path)

        patent_text = get_pdf_text(tmp_path)
        claims = extract_claims(patent_text)

        analysis_start = time.time()
        final_evaluation = analyze_claims(
            claims_text = claims,
            model       = 'Meta-Llama-3.3-70B-Instruct',
            role        = "user",
            api_key     = api_key,
            api_base    = api_base,
            temperature = 0.1,
            top_p       = 1.0,
            max_tokens  = 4096
        )
        app.logger.info(f"Analysis completed in {time.time() - analysis_start:.2f}s")
    finally:
        os.remove(tmp_path)

    return jsonify(final_evaluation)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False, use_reloader=False)
