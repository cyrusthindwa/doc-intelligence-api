import time
import uuid
import hashlib
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Depends
from dependencies.rate_limit import enforce_rate_limit
from fastapi.responses import JSONResponse
from typing import Optional
import json

from services.parser_router import parse_document
from services.ai_extractor import extract, get_active_model, get_active_provider
from services.schema_service import get_schema_fields, get_all_schema_names


router = APIRouter()

# --Constants --
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 # 10MB

SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordpreocessingml.document",
}


# -- Helper - build consistent error response --
def error_resposnse(code: str, message: str, detail: str = None, status: int = 400):
    content = {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "detail": detail,
        },
        "request_id": str(uuid.uuid4()),
    }
    
    return JSONResponse(status_code=status, content=content)


# Helper resolve fields from schema or raw list

def resolve_fields(fields_json: Optional[str], schema: Optional[str]) -> tuple[list[str], str | None]:
    """
    Return (fields_list, error_message).
    Now reads schema definitions from schema_service - single source of truth
    """
    
    #Schema takes priority if provided
    if schema:
        schema = schema.strip().lower()
        fields = get_schema_fields(schema)
        if fields is None:
            available = ", ".join(get_all_schema_names())
            return [], f"Invalid schema '{schema}'. Available: {available}"
        return fields, None
    
    # Otherwise parse the fields JSON array
    if fields_json:
        try:
            fields = json.loads(fields_json)
            if not isinstance(fields, list):
                return [], "fields must be a JSON array e.g. [\"vendor\",\"total\"]"
            if len(fields) == 0:
                return [], "fields array cannot be empty"
            # Clean each field name
            fields = [str(f).strip() for f in fields if str(f).strip()]
            if not fields:
                return [], "fields array contains no valid field names"
            return fields, None
        except json.JSONDecodeError:
            return [], "fields must be valid JSON"
        
    return [], "Either 'fields' or 'schema' is required"


# -- POST /extract --
@router.post("/extract", dependencies=[Depends(enforce_rate_limit)])
async def extract_document(
    file: UploadFile = File(..., description="Document to extract data from"),
    fields: Optional[str] = Form(None, description='JSON array of custom field names e.g. ["vendor_name","total"]'),
    schema_name: Optional[str] = Form(None, description="Predefined schema name. One of: invoice, identity, resume, medical"),
    confidence: Optional[bool] = Form(False, description="Include per-field confidence scores in the response"),
):
    """
    Extract structured data from a document.

    Upload a document (PDF, image, DOCX, or plain text) and extract
    structured fields using AI. You must specify either a `schema_name`
    (predefined template) or `fields` (custom list of field names).

    ---
    Example request (using a predefined schema):
        POST /v1/extract
        Content-Type: multipart/form-data
        x-api-key: <your-api-key>

        file: @invoice.pdf
        schema_name: invoice

    Example response (200):
        {
            "status": "success",
            "request_id": "a1b2c3d4-...",
            "document": {
                "filename": "invoice.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": 245760,
                "page_count": 2,
                "word_count": 340,
                "input_type": "pdf",
                "checksum": "a1b2c3d4e5f6g7h8"
            },
            "extracted_fields": {
                "vendor_name": "Acme Corp",
                "invoice_number": "INV-2024-001",
                "total_amount": "$1,250.00",
                "currency": "USD"
            },
            "metadata": {
                "schema_used": "invoice",
                "fields_requested": ["vendor_name", "invoice_number", "total_amount", "currency"],
                "processing_time_ms": 3450,
                "tokens_used": 892,
                "model": "claude-opus-4-5"
            }
        }

    Example request (custom fields):
        POST /v1/extract
        Content-Type: multipart/form-data
        x-api-key: <your-api-key>

        file: @resume.pdf
        fields: ["name","email","skills"]

    Example response with confidence scores (200):
        {
            "status": "success",
            "request_id": "b2c3d4e5-...",
            "document": { "...": "..." },
            "extracted_fields": {
                "name": "John Doe",
                "email": "john@example.com",
                "skills": ["Python", "FastAPI", "React"]
            },
            "confidence_scores": {
                "name": 0.98,
                "email": 0.99,
                "skills": 0.85
            },
            "metadata": { "...": "..." }
        }

    Example error — missing fields (400):
        {
            "status": "error",
            "error": {
                "code": "INVALID_FIELDS",
                "message": "Either 'fields' or 'schema' is required",
                "detail": "Provide either 'schema' (invoice|identity|resume|medical) or 'fields' as a JSON array."
            },
            "request_id": "c3d4e5f6-..."
        }

    Example error — unsupported file type (400):
        {
            "status": "error",
            "error": {
                "code": "UNSUPPORTED_FILE_TYPE",
                "message": "File type 'application/xml' is not supported.",
                "detail": "Supported types: PDF, PNG, JPEG, WEBP, TXT, DOCX."
            },
            "request_id": "d4e5f6a7-..."
        }
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # -- 1. Validate file was actually attached -- 
    if not file or not file.filename:
        return error_resposnse(
            code="MISSING_FILE",
            message="No file was attached to the request.",
            detail="Attach a file using multipart/form-data with field name 'file'."
        )
        
    #-- 2. Read file bytes
    file_bytes = await file.read()
    
    #-- 3. Validate file size
    file_size = len(file_bytes)
    if file_size == 0:
        return error_resposnse(
            code="EMPTY_FILE",
            message="The uploaded file is empty.",
            detail="Upload a file that contains content"
        )
    
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return error_resposnse(
            code="FILE_TOO_LARGE",
            message=f"File size {size_mb:.1f}MB exceed the 10MB limit.",
            detail="Compress or split the document and try again.",
        )
        
    # -- 4. Validate MIME type --
    mime_type = file.content_type or ""
    
    # Some browsers send image/jpg - normalise it
    if mime_type == "image/jpg":
        mime_type = "image/jpeg"
        
    if mime_type not in SUPPORTED_MIME_TYPES:
        return error_resposnse(
            code="UNSUPPORTED_FILE_TYPE",
            message=f"File type '{mime_type}' is not supported.",
            detail=f"Supported types: PDF, PNG, JPEG, WEBP, TXT, DOCX.",
        )
        
    # -- 5. Validate fields / schema --
    resolved_fields, field_error = resolve_fields(fields, schema_name)
    if field_error:
        return error_resposnse(
            code="INVALID_FIELDS",
            message=field_error,
            detail="Provide either 'schema' (invoice|identity|resume|medical) or 'fields' as a JSON array.",
        )
        
    # -- 6. Parse the document --
    parsed = parse_document(
        file_bytes=file_bytes,
        mime_type=mime_type,
        filename=file.filename,
    )
    if not parsed["success"]:
        return error_resposnse(
            code="PARSED_FAILED",
            message="The document could not be parsed",
            detail=parsed.get("error"),
            status=422,
        )
        
    #-- 7. Extract fields with Claude --
    extraction = extract(parsed_document=parsed,fields=resolved_fields)
    
    if not extraction["success"]:
        return error_resposnse(
            code="EXTRACTION_FAILED",
            message="Field extraction failed",
            detail=extraction.get("error"),
            status=500,
        )
        
    # -- 8. Build success response --
    processing_ms = int((time.time() - start_time) * 1000)
    checksum = hashlib.sha256(file_bytes).hexdigest()[:16]
    
    response_body = {
        "status": "success",
        "request_id": request_id,
        "document": {
            "filename": file.filename,
            "mime_type": mime_type,
            "file_size_bytes": file_size,
            "page_count": parsed.get("page_count"),
            "word_count": parsed.get("word_count"),
            "input_type": parsed.get("input_type"),
            "checksum": checksum,
        },
        "extracted_fields": extraction["extracted_fields"],
        "metadata": {
            "schema_used": schema_name or "custom",
            "fields_requested": resolved_fields,
            "processing_time_ms": processing_ms,
            "tokens_used": extraction.get("tokens_used"),
            "model": get_active_model(),
            "provider": get_active_provider(),
        },
    }

    # Optionally include confidence scores
    if confidence and extraction.get("confidence_scores"):
        response_body["confidence_scores"] = extraction["confidence_scores"]

    return JSONResponse(status_code=200, content=response_body)

