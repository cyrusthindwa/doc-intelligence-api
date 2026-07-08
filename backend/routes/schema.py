from fastapi import APIRouter
from fastapi.responses import JSONResponse
from services.schema_service import (
    get_schema_definition,
    get_all_schemas_summary,
    get_all_schema_names,
)

router = APIRouter()


@router.get("/schema")
async def list_schemas():
    """
    List all predefined schemas.

    Returns a summary of every available extraction schema, including
    the display name, description, and number of fields in each.

    ---
    Example request:
        GET /v1/schema

    Example response (200):
        {
            "status": "success",
            "count": 4,
            "schemas": [
                {
                    "name": "invoice",
                    "display_name": "Invoice",
                    "description": "Extract structured data from invoice and billing documents",
                    "field_count": 10
                },
                {
                    "name": "identity",
                    "display_name": "Identity Document",
                    "description": "Extract data from ID cards, passports, and driving licences",
                    "field_count": 8
                },
                {
                    "name": "resume",
                    "display_name": "Resume / CV",
                    "description": "Extract professional information from resumes and CVs",
                    "field_count": 9
                },
                {
                    "name": "medical",
                    "display_name": "Medical Form",
                    "description": "Extract data from medical forms, prescriptions, and patient records",
                    "field_count": 8
                }
            ]
        }
    """
    schemas = get_all_schemas_summary()

    return JSONResponse(status_code = 200, content={
        "status": "success",
        "count": len(schemas),
        "schemas": schemas
    })

@router.get("/schema/{schema_type}")
async def get_schema(schema_type: str):
    """
    Get a single schema definition with full field details.

    Returns the complete schema definition including field names,
    data types, and descriptions for each field.

    ---
    Example request:
        GET /v1/schema/invoice

    Example response (200):
        {
            "status": "success",
            "name": "invoice",
            "display_name": "Invoice",
            "description": "Extract structured data from invoice and billing documents",
            "fields": [
                {
                    "name": "vendor_name",
                    "type": "string",
                    "description": "Company or individual that issued the invoice"
                },
                {
                    "name": "total_amount",
                    "type": "string",
                    "description": "Final total including all taxes"
                },
                "..."
            ]
        }

    Example error — schema not found (404):
        {
            "status": "error",
            "error": {
                "code": "SCHEMA_NOT_FOUND",
                "message": "Schema 'unknown' does not exist.",
                "detail": "Available schemas: invoice, identity, resume, medical"
            }
        }
    """
    schema_type = schema_type.strip().lower()
    definition = get_schema_definition(schema_type)

    if not definition:
        available = ", ".join(get_all_schema_names())
        return JSONResponse(status_code=404, content={
            "status": "error",
            "error": {
                "code": "SCHEMA_NOT_FOUND",
                "message": f"Schema '{schema_type}' does not exist.",
                "detail": f"Available schemas: {available}"
            }
        })
    return JSONResponse(status_code=200, content={
        "status": "success",
        **definition
    })