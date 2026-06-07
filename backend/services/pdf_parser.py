import fitz # PyMuPDF
import os


def extract_text_from_pdf(file_bytes: bytes) -> dict:
    """
    Extract all text from a PDF file given its raw bytes.
    Return a dict with the text content and metadata.
    """
    try:
        # Open the pdf from bytes (not a file path)
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        full_text = []
        page_count = doc.page_count
        
        # Loop through every page and extract text
        for page_num in range(page_count):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text.strip():
                full_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                
        doc.close()
        
        combined_text = "\n\n".join(full_text)
        word_count = len(combined_text.split())
        
        return {
            "success": True,
            "text": combined_text,
            "page_count": page_count,
            "word_count": word_count,
            "error": None,
        }
        
    except fitz.FileDataError:
        return {
            "success": False,
            "text": None,
            "page_count": 0,
            "word_count": 0,
            "error": "CORRUPT_FILE: PDF could not be opened. It may be damaged.",
        }
        
    except Exception as e:
        return {
            "success": False,
            "text": None,
            "page_count": 0,
            "word_count": 0,
            "error": f"PDF_PARSE_ERROR: {str(e)}",
        }
        
def is_scanned_pdf(file_bytes: bytes) -> bool:
    """
    Check if a PDF is scanned (image-only, no text layer).
    Scanned PDFs need to be sent to claude vision instead of text extraction.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        total_text = ""
        
        for page_num in range(min(3, doc.page_count)): # check first 3 pages
            page = doc[page_num]
            total_text += page.get_text("text")
        
        doc.close()
        
        # if fewer than 50 characters across 3 pages, it is likely scanned
        return len(total_text.strip()) < 50
    
    except Exception:
        # If we can't open the PDF, assume it's not scanned (let extraction handle the error)
        return False
        