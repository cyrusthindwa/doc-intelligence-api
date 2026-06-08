"""
Run this script to verify all parsers are working.

Usage:
    python test_parsers.py

Place real test files in backend/test_files/ before running.
"""

import os
import sys

# Add backend to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pdf_parser import extract_text_from_pdf, is_scanned_pdf
from services.image_parser import validate_and_prepare_image
from services.text_parser import extract_text_from_txt, extract_text_from_docx
from services.parser_router import parse_document


TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")


def load_file(filename: str) -> bytes:
    path = os.path.join(TEST_FILES_DIR, filename)
    if not os.path.exists(path):
        print(f"  ⚠  File not found: {path}")
        return None
    with open(path, "rb") as f:
        return f.read()


def print_result(label: str, result: dict):
    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"{'='*55}")
    print(f"  Success    : {result.get('success')}")
    print(f"  Input type : {result.get('input_type', 'N/A')}")
    print(f"  Word count : {result.get('word_count', 'N/A')}")
    print(f"  Page count : {result.get('page_count', 'N/A')}")
    print(f"  Error      : {result.get('error')}")

    if result.get("text"):
        preview = result["text"][:300].replace("\n", " ")
        print(f"  Text preview: ...{preview}...")

    if result.get("base64_data"):
        preview = result["base64_data"][:60]
        print(f"  Base64 preview: {preview}...")
        print(f"  Image MIME  : {result.get('mime_type')}")


def run_tests():
    print("\n  Document Parser Test Suite")
    print(f"    Test files directory: {TEST_FILES_DIR}\n")

    if not os.path.exists(TEST_FILES_DIR):
        os.makedirs(TEST_FILES_DIR)
        print(f"  Created test_files/ directory.")
        print(f"  Add these files to it and re-run:")
        print(f"    - sample.pdf")
        print(f"    - sample.png  or  sample.jpg")
        print(f"    - sample.txt")
        print(f"    - sample.docx")
        return

    # ── Test 1: PDF ───────────────────────────────────────────────
    print("\n  TEST 1 — PDF Parser")
    pdf_bytes = load_file("sample.pdf")
    if pdf_bytes:
        scanned = is_scanned_pdf(pdf_bytes)
        print(f"  Is scanned PDF: {scanned}")
        result = parse_document(pdf_bytes, "application/pdf", "sample.pdf")
        print_result("PDF via parser_router", result)

    # ── Test 2: PNG Image ─────────────────────────────────────────
    print("\n   TEST 2 — Image Parser (PNG)")
    png_bytes = load_file("sample.png")
    if not png_bytes:
        png_bytes = load_file("sample.jpg")
        mime = "image/jpeg"
        name = "sample.jpg"
    else:
        mime = "image/png"
        name = "sample.png"

    if png_bytes:
        result = parse_document(png_bytes, mime, name)
        print_result("Image via parser_router", result)

    # ── Test 3: Plain text ────────────────────────────────────────
    print("\n  TEST 3 — Text Parser (.txt)")
    txt_bytes = load_file("sample.txt")
    if txt_bytes:
        result = parse_document(txt_bytes, "text/plain", "sample.txt")
        print_result("TXT via parser_router", result)

    # ── Test 4: Word document ─────────────────────────────────────
    print("\n  TEST 4 — DOCX Parser (.docx)")
    docx_bytes = load_file("sample.docx")
    if docx_bytes:
        result = parse_document(
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "sample.docx"
        )
        print_result("DOCX via parser_router", result)

    # ── Test 5: Quick inline text test (no file needed) ───────────
    print("\n  TEST 5 — Inline TXT (no file needed)")
    sample_text = b"This is a test document.\nIt has two lines.\nParsing should work fine."
    result = parse_document(sample_text, "text/plain", "inline_test.txt")
    print_result("Inline TXT", result)

    print(f"\n{'='*55}")
    print("  Test run complete.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run_tests()