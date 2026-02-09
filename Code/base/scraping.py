# brew install poppler
# brew install tesseract
import re
import os
import tempfile
import pdfplumber
import pytesseract
import pathlib
from pdf2image import convert_from_path
from PIL import Image

# ---- AWS-friendly knobs (set via env vars, defaults are safe) ----
TAIL_TEXT_PAGES = int(os.getenv("TAIL_TEXT_PAGES", "20"))    # last N pages to try with pdfplumber
TAIL_OCR_PAGES = int(os.getenv("TAIL_OCR_PAGES", "20"))     # last N pages to OCR if needed
OCR_DPI = int(os.getenv("OCR_DPI", "200"))           # 300 is heavy on EC2
OCR_TIMEOUT = int(os.getenv("OCR_TIMEOUT", "25"))        # seconds per page
OCR_LANG = os.getenv("OCR_LANG", "eng")

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

def pdf_to_text_ocr(pdf_path: str, first_page: int, last_page: int) -> str:
    """
    Convert only a page range to text using OCR.
    Uses paths_only=True so we don't keep all images in memory.
    """
    text_pages = []
    with tempfile.TemporaryDirectory() as tempdir:
        image_paths = convert_from_path(
            pdf_path,
            dpi=OCR_DPI,
            output_folder=tempdir,
            first_page=first_page,
            last_page=last_page,
            fmt="jpeg",
            paths_only=True,   # ✅ keeps memory bounded
            thread_count=2,
        )

        for page_num, img_path in enumerate(image_paths, start=first_page):
            try:
                with Image.open(img_path) as img:
                    page_text = pytesseract.image_to_string(
                        img,
                        lang=OCR_LANG,
                        timeout=OCR_TIMEOUT,  # ✅ prevents hangs
                        config="--psm 6"
                    )
                text_pages.append(page_text)
            except RuntimeError:
                # pytesseract timeout often raises RuntimeError
                text_pages.append(f"\n[OCR TIMEOUT page {page_num} after {OCR_TIMEOUT}s]\n")
            except pytesseract.TesseractError as e:
                text_pages.append(f"\n[OCR ERROR page {page_num}]: {e}\n")

    return "\n".join(text_pages)

def get_pdf_text(pdf_path: str) -> str:
    """
    Tail-first extraction:
    - Cache to .tail.txt
    - Try embedded text from last TAIL_TEXT_PAGES pages
    - If empty, OCR only last TAIL_OCR_PAGES pages
    """
    pdf_path = str(pdf_path)
    txt_path = pathlib.Path(pdf_path).with_suffix(".tail.txt")

    # Determine total pages
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

    # 1) Fast: extract embedded text from tail pages
    start_text_page = max(0, total_pages - TAIL_TEXT_PAGES)
    embedded_chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for i in range(start_text_page, total_pages):
            embedded_chunks.append(pdf.pages[i].extract_text() or "")
    full_text = "\n".join(embedded_chunks)

    # 2) If basically empty, OCR only the tail pages
    if len(full_text.strip()) < 50:
        first_ocr_page = max(1, total_pages - TAIL_OCR_PAGES + 1)  # 1-indexed
        last_ocr_page = total_pages
        print(
            f"[INFO] No readable text found in tail of {pdf_path}. "
            f"Using OCR pages {first_ocr_page}-{last_ocr_page} (dpi={OCR_DPI})..."
        )
        full_text = pdf_to_text_ocr(pdf_path, first_page=first_ocr_page, last_page=last_ocr_page)

    # Save cache
    txt_path.write_text(full_text, encoding="utf-8")
    return full_text