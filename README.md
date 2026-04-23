# PatentNerd

**PatentNerd** is an AI-powered tool that helps inventors and patent attorneys write stronger patent claims. Upload a patent PDF and receive a structured analysis across multiple dimensions of claim quality.

Built by Yuge Duan, Abigail Beckler, and Dennis Shasha.

---

## What it does

Patents are judged on three criteria: novelty, clarity of disclosure, and breadth of claims. PatentNerd focuses on criteria (ii) and (iii) — whether the patent body clearly supports the claims, and whether the claims cover the full scope of the invention.

Given a patent PDF, PatentNerd runs the claims through a series of LLM-powered analyses:

| Analysis | What it checks |
|---|---|
| **Clarity & Sufficiency** | Technical nouns/verbs that are ambiguous across fields or jargon that needs defining |
| **Antecedent Issues** | Terms used in claims without prior definition; undefined acronyms |
| **Semantic Ambiguity** | Polysemous words, vague degree terms, inconsistent synonyms, unclear pronouns |
| *(+ additional prompts)* | Further claim-quality checks defined in `Code/base/openai_prompts.py` |

The backend is a Flask API. The model runs via [SambaNova](https://sambanova.ai/) using a `Meta-Llama-3.3-70B-Instruct` model through an OpenAI-compatible API.

---

## Prerequisites

Before installing, make sure you have the following on your system:

- **Python 3.10+**
- **Poppler** — required by `pdf2image` for PDF rendering
  ```bash
  # macOS
  brew install poppler

  # Ubuntu/Debian
  sudo apt-get install poppler-utils
  ```
- **Tesseract** — required by `pytesseract` for OCR on image-based PDFs
  ```bash
  # macOS
  brew install tesseract

  # Ubuntu/Debian
  sudo apt-get install tesseract-ocr
  ```

---

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/abeckler21/patentnerd.git
   cd patentnerd
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv

   # macOS/Linux
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your API key**

   PatentNerd uses SambaNova's OpenAI-compatible API. Get a key at [sambanova.ai](https://sambanova.ai/), then set it as an environment variable.

   Option A — export in your shell (temporary, per session):
   ```bash
   export OPENAI_API_KEY="your-sambanova-key-here"
   ```

   Option B — create a `.env` file in the project root (persists across sessions):
   ```
   OPENAI_API_KEY=your-sambanova-key-here
   ```
   Then load it before running:
   ```bash
   set -a && source .env && set +a
   ```

   The API base URL defaults to `https://api.sambanova.ai/v1`. To use a different provider, also set:
   ```bash
   export OPENAI_API_BASE="https://your-provider.com/v1"
   ```

---

## Running the app

```bash
python Code/app.py
```

The server starts at `http://127.0.0.1:8000`.

---

## API

### `POST /analyze`

Upload a patent PDF for analysis.

**Request** — `multipart/form-data`:
| Field | Type | Description |
|---|---|---|
| `patent` | file | A `.pdf` file of the patent to analyze |

**Response** — `application/json`:
```json
{
  "Clarity_and_sufficiency": "...",
  "Antecedent_issues": "...",
  "Semantic_ambiguity": "..."
}
```
Each key is a prompt name and each value is the LLM's analysis for that dimension. If a prompt fails, its value will contain an error message rather than causing the whole request to fail.

**Example with curl:**
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -F "patent=@/path/to/your/patent.pdf"
```

---

## Project structure

```
patentnerd-backend/
├── Code/
│   ├── app.py                  # Flask app and API routes
│   └── base/
│       ├── scraping.py         # PDF text extraction and OCR
│       ├── patent_logic.py     # LLM call orchestration
│       └── openai_prompts.py   # Prompt definitions
├── requirements.txt
└── README.md
```
