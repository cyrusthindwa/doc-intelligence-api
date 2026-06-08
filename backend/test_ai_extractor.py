"""
Test the full pipeline: parse document → extract fields with Claude.

Usage:
    python test_ai_extractor.py

Requires real files in backend/test_files/
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.parser_router import parse_document
from services.ai_extractor import extract


TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")


def load_file(filename: str) -> bytes:
    path = os.path.join(TEST_FILES_DIR, filename)
    if not os.path.exists(path):
        print(f"  ⚠  Not found: {path} — skipping")
        return None
    with open(path, "rb") as f:
        return f.read()


def print_result(label: str, result: dict):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Success     : {result.get('success')}")
    print(f"  Tokens used : {result.get('tokens_used')}")
    print(f"  Error       : {result.get('error')}")
    print(f"\n  Extracted fields:")
    fields = result.get("extracted_fields", {})
    print(json.dumps(fields, indent=4))


def run():
    print("\n🤖  AI Extractor Test Suite")
    print(f"    Using model: claude-opus-4-5\n")

    # ── Test 1: PDF Invoice ───────────────────────────────────────
    print("\n📄  TEST 1 — PDF Invoice")
    pdf_bytes = load_file("sample.pdf")
    if pdf_bytes:
        parsed = parse_document(pdf_bytes, "application/pdf", "sample.pdf")
        print(f"  Parser result: success={parsed['success']}, "
              f"type={parsed['input_type']}, words={parsed['word_count']}")

        result = extract(parsed, fields=[
            "vendor_name",
            "invoice_number",
            "invoice_date",
            "due_date",
            "total_amount",
            "tax_amount",
            "line_items",
        ])
        print_result("Invoice extraction", result)

    # ── Test 2: Image (ID card or any image with text) ────────────
    print("\n🖼   TEST 2 — Image")
    img_bytes = load_file("sample.png")
    mime = "image/png"
    name = "sample.png"

    if not img_bytes:
        img_bytes = load_file("sample.jpg")
        mime = "image/jpeg"
        name = "sample.jpg"

    if img_bytes:
        parsed = parse_document(img_bytes, mime, name)
        print(f"  Parser result: success={parsed['success']}, "
              f"type={parsed['input_type']}")

        result = extract(parsed, fields=[
            "full_name",
            "date_of_birth",
            "id_number",
            "expiry_date",
            "nationality",
        ])
        print_result("Image extraction", result)

    # ── Test 3: Plain text Resume ─────────────────────────────────
    print("\n📝  TEST 3 — Plain Text Resume")

    # Use a real file if available, otherwise create inline sample
    txt_bytes = load_file("sample_resume.txt")

    if not txt_bytes:
        # Inline sample so Test 3 always runs even without a file
        sample_resume = """
John Banda
Software Developer
Email: john.banda@email.com | Phone: +265 999 123 456
Location: Blantyre, Malawi

SUMMARY
Experienced full-stack developer with 4 years building web applications
using Python, React, and PostgreSQL. Delivered 6 production systems.

SKILLS
Python, FastAPI, React, PostgreSQL, Docker, Git, REST APIs, JavaScript

EXPERIENCE
Senior Developer — TechMalawi Ltd (2022 - Present)
- Built school management system used by 12 schools
- Developed REST API serving 500 daily active users

Junior Developer — StartupMW (2020 - 2022)
- Maintained e-commerce platform with 2000 products
- Integrated mobile money payment gateway

EDUCATION
BSc Computer Science — University of Malawi (2016 - 2020)
        """
        txt_bytes = sample_resume.encode("utf-8")
        print("  (Using inline sample resume — add sample_resume.txt to test_files/ for a real test)")

    parsed = parse_document(txt_bytes, "text/plain", "resume.txt")
    print(f"  Parser result: success={parsed['success']}, words={parsed['word_count']}")

    result = extract(parsed, fields=[
        "full_name",
        "email",
        "phone",
        "location",
        "skills",
        "years_of_experience",
        "current_employer",
        "education",
    ])
    print_result("Resume extraction", result)

    # ── Test 4: Edge case — empty document ────────────────────────
    print("\n⚠️   TEST 4 — Edge case: empty document")
    empty_bytes = b""
    parsed = parse_document(empty_bytes, "text/plain", "empty.txt")
    result = extract(parsed, fields=["name", "date"])
    print_result("Empty document", result)

    print(f"\n{'='*60}")
    print("  Test run complete.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run()