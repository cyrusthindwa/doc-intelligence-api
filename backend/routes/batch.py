import asyncio
import time
import uuid
import json
from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import Optional

from services.parser_router import parse_document
from services.ai_extractor import extract
from services.schema_service import get_schema_fields, get_all_schema_names
from dependencies.rate_limit import enforce_rate_limit

router = APIRouter()

MAX_BATCH_SIZE = 10
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def error_response(code: str, message: str, detail: str = None, status: int = 400):
    return JSONResponse(status_code=status, content={
        "status": "error",
        "error": {"code": code, "message": message, "detail": detail},
        "request_id": str(uuid.uuid4()),
    })


def resolve_batch_fields(fields_json: Optional[str], schema_name: Optional[str]):
    if schema_name:
        schema_name = schema_name.strip().lower()
        fields = get_schema_fields(schema_name)
        if fields is None:
            available = ", ".join(get_all_schema_names())
            return [], f"Invalid schema '{schema_name}'. Available: {available}"
        return fields, None

    if fields_json:
        try:
            fields = json.loads(fields_json)
            if not isinstance(fields, list) or len(fields) == 0:
                return [], "fields must be a non-empty JSON array"
            return [str(f).strip() for f in fields if str(f).strip()], None
        except json.JSONDecodeError:
            return [], "fields must be valid JSON"

    return [], "Either 'fields' or 'schema' is required"


async def process_single_file(file: UploadFile, fields: list[str], index: int) -> dict:
    """
    Process one file in the batch. Never raises — always returns a result dict,
    even on failure, so one bad file doesn't kill the whole batch.
    """
    try:
        file_bytes = await file.read()
        filename = file.filename or f"file_{index}"

        # Validate size
        if len(file_bytes) == 0:
            return {"index": index, "filename": filename, "status": "failed", "error": "EMPTY_FILE: File has no content"}

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            return {"index": index, "filename": filename, "status": "failed", "error": "FILE_TOO_LARGE: Exceeds 10MB limit"}

        # Validate mime type
        mime_type = file.content_type or ""
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"

        if mime_type not in SUPPORTED_MIME_TYPES:
            return {"index": index, "filename": filename, "status": "failed", "error": f"UNSUPPORTED_FILE_TYPE: {mime_type}"}

        # Parse
        parsed = parse_document(file_bytes=file_bytes, mime_type=mime_type, filename=filename)
        if not parsed["success"]:
            return {"index": index, "filename": filename, "status": "failed", "error": f"PARSE_FAILED: {parsed.get('error')}"}

        # Extract
        extraction = extract(parsed_document=parsed, fields=fields)
        if not extraction["success"]:
            return {"index": index, "filename": filename, "status": "failed", "error": f"EXTRACTION_FAILED: {extraction.get('error')}"}

        return {
            "index": index,
            "filename": filename,
            "status": "success",
            "extracted_fields": extraction["extracted_fields"],
            "tokens_used": extraction.get("tokens_used"),
        }

    except Exception as e:
        return {"index": index, "filename": file.filename or f"file_{index}", "status": "failed", "error": f"UNEXPECTED_ERROR: {str(e)}"}


@router.post("/batch", dependencies=[Depends(enforce_rate_limit)])
async def batch_extract(
    files: list[UploadFile] = File(..., description="Up to 10 documents"),
    fields: Optional[str] = Form(None, description='JSON array applied to all documents'),
    schema_name: Optional[str] = Form(None, description="Predefined schema applied to all documents"),
):
    start_time = time.time()

    # Validate batch size
    if len(files) == 0:
        return error_response("MISSING_FILES", "No files were attached to the request.")

    if len(files) > MAX_BATCH_SIZE:
        return error_response(
            "BATCH_TOO_LARGE",
            f"Batch contains {len(files)} files, exceeding the limit of {MAX_BATCH_SIZE}.",
            detail="Split into smaller batches and retry."
        )

    # Resolve fields once — applied to every document in the batch
    resolved_fields, field_error = resolve_batch_fields(fields, schema_name)
    if field_error:
        return error_response("INVALID_FIELDS", field_error)

    # Process all files concurrently using asyncio.gather
    # This is the key performance win — 10 files process in parallel,
    # not sequentially, so total time ≈ slowest single file, not the sum of all.
    tasks = [
        process_single_file(file, resolved_fields, index)
        for index, file in enumerate(files)
    ]
    results = await asyncio.gather(*tasks)

    processed = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    processing_ms = int((time.time() - start_time) * 1000)

    return JSONResponse(status_code=200, content={
        "status": "success",
        "total_documents": len(files),
        "processed": processed,
        "failed": failed,
        "processing_time_ms": processing_ms,
        "results": results,
    })