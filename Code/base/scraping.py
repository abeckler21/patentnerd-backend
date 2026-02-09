# brew install poppler
# brew install tesseract
import re
import tempfile
import pdfplumber
import pytesseract
import pathlib
from pdf2image import convert_from_path

# Common INID code patterns for metadata
INID_CODES = {
    'title': r'\(54\)\s*(.*)',
    'abstract': r'\(57\)\s*(.*)',
    'patent_number': r'\(11\)\s*(.*)',
    'application_number': r'\(21\)\s*(.*)',
    'priority_claim': r'\(30\)\s*(.*?)(?:\n\(|$)',
    'issue_date': r'\(45\)\s*(.*)',
    'inventor': r'\(72\)\s*(.*)',
    'assignee': r'\(71\)\s*(.*)',
}

# Free-text section headings (these vary by patent)
TEXT_SECTIONS = {
    'Background of the Invention': ["BACKGROUND", "BACKGROUND OF THE INVENTION"],
    'Summary of the Invention': ["SUMMARY", "SUMMARY OF THE INVENTION"],
    'Brief Description of the Invention': ["BRIEF DESCRIPTION OF THE INVENTION"],
    'Brief Description of the Figures': ["BRIEF DESCRIPTION OF THE DRAWINGS", "BRIEF DESCRIPTION OF THE FIGURES"],
    'Detailed Description of the Invention': ["DETAILED DESCRIPTION", "DETAILED DESCRIPTION OF THE INVENTION"]
}

def remove_line_numbers(text):
    """Remove line numbers from patent text."""
    return re.sub(r'^\s*\d+\s+', '', text, flags=re.MULTILINE)

def extract_inid_metadata(first_page_text):
    """Extract metadata using INID codes (wonky with page 1 misalignment)"""
    data = {}
    for key, pattern in INID_CODES.items():
        m = re.search(pattern, first_page_text)
        data[key] = m.group(1).strip() if m else ''
    return data

def extract_text_sections(full_text: str):
    """Extract relevant sections from the text"""
    # Normalize spacing, capture and split headers
    text = re.sub(r'\s+', ' ', full_text)
    section_patterns = []
    for canon, variants in TEXT_SECTIONS.items():
        for v in variants:
            section_patterns.append(re.escape(v))
    section_regex = r'(' + '|'.join(section_patterns) + r')'
    parts = re.split(section_regex, text)

    # Extract text
    sections = {}
    current_header = None
    for part in parts:
        if not part.strip():
            continue
        # If part is a header
        for canon, variants in TEXT_SECTIONS.items():
            if part.upper() in [v.upper() for v in variants]:
                current_header = canon
                sections[current_header] = ""
                break
        else:
            # Otherwise, treat as body text
            if current_header:
                sections[current_header] += part.strip() + " "

    # Strip trailing spaces
    return {k: v.strip() for k, v in sections.items()}
        

def extract_claims(full_text):
    """Find the last '1.' numbered list and grab until end."""
    text = remove_line_numbers(full_text)
    matches = list(re.finditer(r'\n\s*1\.\s+', text))
    if not matches:
        return ""
    start_index = matches[-1].start()
    return text[start_index:].strip()

def pdf_to_text_ocr(pdf_path):
    """Convert PDF to text using OCR."""
    text_pages = []
    with tempfile.TemporaryDirectory() as tempdir:
        images = convert_from_path(pdf_path, dpi=300, output_folder=tempdir)
        for img in images:
            page_text = pytesseract.image_to_string(img)
            text_pages.append(page_text)
    return "\n".join(text_pages)

def get_pdf_text(pdf_path):
    """Try pdfplumber first; if no text found, use OCR."""
    # derive the corresponding txt file name
    txt_path = pathlib.Path(pdf_path).with_suffix(".txt")
    if txt_path.exists():
        print(f"[INFO] Found existing {txt_path}, skipping scraping.")
        with open(txt_path, "r", encoding="utf-8") as f:
            full_text = f.read()
    else:
        with pdfplumber.open(pdf_path) as pdf:
            pages = [page.extract_text() or '' for page in pdf.pages]
        full_text = "\n".join(pages)

        # Check if we actually got text (not just whitespace)
        if len(full_text.strip()) < 50:
            print(f"[INFO] No readable text found in {pdf_path}. Using OCR...")
            full_text = pdf_to_text_ocr(pdf_path)
        
        # save to txt
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_text)

    return full_text