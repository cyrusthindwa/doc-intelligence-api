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
    List all availabel predefined schemas
    Returns name, description and field count for each.
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
    Return all full field definition for a specific schema.
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