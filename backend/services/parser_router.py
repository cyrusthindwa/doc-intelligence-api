from services.pdf_parser import extract_text_from_pdf, is_scanned_pdf
from services.image_parser import validate_and_prepare_image
from services.text_parser import extract_text


def parse_document(file_bytes: bytes, mime_type: str, filename: str) -> dict:
    """
    Master router. Given a file, return either:
    - extracted text (for PDF, TXT, DOCX) -> ready for Claude text API
    - base64 image data (for PNG, JPEG) -> ready for Claude vision API
    
    Always return the same dict shape so callers don't need to branch.
    """
    
    # --Images -> prepare for Claude vision ---
    if mime_type in ("image/png", "image/jpeg", "image/jpg", "image/webp"):
        result = validate_and_prepare_image(file_bytes, mime_type)
        return {
            "success": result["success"],
            "input_type": "image",
            "text": None,
            "base64_data": result.get("base64_data"),
            "mime_type": result.get("mime_type"),
            "page_count": 1,
            "word_count": 0,
            "filename": filename,
            "error": result.get("error")
        }
        
    # -- PDFs -> extract text (unless scanned)
    if mime_type == "application/pdf":
        # Check if it is a scanned PDF first
        if is_scanned_pdf(file_bytes):
            # Scanned PDF - treat as image, send to Claude vision
            image_result = validate_and_prepare_image(file_bytes, "image/png")
            return {
                "success": image_result["success"],
                "input_type": "scanned_pdf",
                "text": None,
                "base64_data": image_result.get("base64_data"),
                "mime_type": "image/png",
                "page_count": 0,
                "word_count": 0,
                "filename": filename,
                "error": image_result.get("error")
            }
            
        # Regular PDF with text layer
        result = extract_text_from_pdf(file_bytes)
        return {
            "success": result["success"],
            "input_type": "text",
            "text": result.get("text"),
            "base64_data": None,
            "mime_type": mime_type,
            "page_count": result.get("page_count", 0),
            "word_count": result.get("word_count", 0),
            "filename": filename,
            "error": result.get("error")
        }
        
    # -- TXT and DOCX -> extract text
    result = ectract_text(file_bytes, mime_type)
    return {
        "success": result["success"],
        "input_type": "text",
        "text": result.get("text"),
        "base64_data": None,
        "mime_type": mime_type,
        "page_count": 1,
        "word_count": result.get("word_count", 0),
        "filename": filename,
        "error": result.get("error"), 
    }
    
