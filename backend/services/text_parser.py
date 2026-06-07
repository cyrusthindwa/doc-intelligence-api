import io
import docx # python-docx


def extract_text_from_txt(file_bytes: bytes) -> dict:
    """
    Extract text from a plain .txt file
    Tries UTF-8 first, falls back to latin-1 for older files.
    """
    
    try:
        # Try UTF-8 first (covers 99% of modern files)
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # Fall back to latin-1 which never fails
            text = file_bytes.decode("latin-1")
            
        text = text.strip()
        word_count = len(text.split())
        
        if not text:
            return {
                "success": False,
                "text": None,
                "word_count": 0,
                "error": "EMPTY_FILE: The text file contains no content."
            }
            
        return {
            "success": True,
            "text": text,
            "word_count": word_count,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "text": None,
            "word_count": 0,
            "error": f"TEXT_PARSE_ERROR: {str(e)}"
        }
        
def extract_text_from_docx(file_bytes: bytes) -> dict:
    """
    Ectract text from a .docx Word document.
    Extracts paragraph text in order. Tables are also extracted.
    """
    try:
        # python-docx needs a file-like object, not raw bytes
        file_stream = io.BytesIO(file_bytes)
        document = docx.Document(file_stream)
        
        extracted_parts = []
        
        # Extract all paragraphs in document order
        for para in document.parahraphs:
            text = para.text.strip()
            if text:
                extracted_parts.append(text)
        
        # Extract text from tables too
        for table in document.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        row_text.append(cell_text)
                if row_text:
                    extracted_parts.append(" | ".join(row_text))
                    
        if not extracted_parts:
            return {
                "success": False,
                "text": None,
                "word_count": 0,
                "error": "EMPTY_DOCUMENT: The document contains no readable text."
            }
            
        full_text = "\n".join(extracted_parts)
        word_count = len(full_text.split())
        
        return {
            "success": True,
            "text": full_text,
            "word_count": word_count,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "text": None,
            "word_count": 0,
            "error": f"DOCX_PARSE_ERROR: {str(e)}"
        }
        
def extract_text(file_bytes: bytes, mime_type: str) -> dict:
    """
    Router function - picks the right parser based on mime type.
    Call this from routes instead of the individual functions.
    """
    if mime_type == "text/plain":
        return extract_text_from_txt(file_bytes)
    elif mime_type in( 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/docx",
    ):
        return extract_text_from_docx(file_bytes)
    else:
        return {
            "success": False,
            "text": None,
            "word_count": 0,
            "error": f"UNSUPPORTED_FORMAT: No text parser for {mime_type}"
        }