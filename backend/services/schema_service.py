from unicodedata import name
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from models.schemas import Schema


#  Schema definition
# These are the canonical field lists for each predefined schema.
# Stored in the database so they can be updated without code changes.

SCHEMA_DEFINITIONS = {
    "invoice": {
        "display_name": "Invoice",
        "description": "Extract structured data from invoice and billing documents",
        "fields": [
            {"name": "vendor_name",    "type": "string", "description": "Company or individual that issued the invoice"},
            {"name": "vendor_address", "type": "string", "description": "Full address of the vendor"},
            {"name": "invoice_number", "type": "string", "description": "Unique invoice identifier"},
            {"name": "invoice_date",   "type": "string", "description": "Date the invoice was issued"},
            {"name": "due_date",       "type": "string", "description": "Payment due date"},
            {"name": "subtotal",       "type": "string", "description": "Amount before tax"},
            {"name": "tax_amount",     "type": "string", "description": "Total tax applied"},
            {"name": "total_amount",   "type": "string", "description": "Final total including all taxes"},
            {"name": "currency",       "type": "string", "description": "Currency code or symbol"},
            {"name": "line_items",     "type": "array",  "description": "Individual items listed on the invoice"},
        ]
    },
    "identity": {
        "display_name": "Identity Document",
        "description": "Extract data from ID cards, passports, and driving licences",
        "fields": [
            {"name": "full_name",      "type": "string", "description": "Full legal name as printed"},
            {"name": "date_of_birth",  "type": "string", "description": "Date of birth"},
            {"name": "id_number",      "type": "string", "description": "National ID, passport, or licence number"},
            {"name": "document_type",  "type": "string", "description": "Type of identity document"},
            {"name": "issue_date",     "type": "string", "description": "Date the document was issued"},
            {"name": "expiry_date",    "type": "string", "description": "Date the document expires"},
            {"name": "nationality",    "type": "string", "description": "Nationality or country of issue"},
            {"name": "gender",         "type": "string", "description": "Gender as printed on document"},
        ]
    },
    "resume": {
        "display_name": "Resume / CV",
        "description": "Extract professional information from resumes and CVs",
        "fields": [
            {"name": "full_name",       "type": "string", "description": "Candidate full name"},
            {"name": "email",           "type": "string", "description": "Email address"},
            {"name": "phone",           "type": "string", "description": "Phone number"},
            {"name": "location",        "type": "string", "description": "City, country or address"},
            {"name": "summary",         "type": "string", "description": "Professional summary or objective"},
            {"name": "skills",          "type": "array",  "description": "List of technical and soft skills"},
            {"name": "work_experience", "type": "array",  "description": "Employment history with roles and dates"},
            {"name": "education",       "type": "array",  "description": "Academic qualifications and institutions"},
            {"name": "certifications",  "type": "array",  "description": "Professional certifications"},
        ]
    },
    "medical": {
        "display_name": "Medical Form",
        "description": "Extract data from medical forms, prescriptions, and patient records",
        "fields": [
            {"name": "patient_name",  "type": "string", "description": "Full name of the patient"},
            {"name": "patient_dob",   "type": "string", "description": "Patient date of birth"},
            {"name": "doctor_name",   "type": "string", "description": "Attending doctor or physician name"},
            {"name": "diagnosis",     "type": "string", "description": "Primary diagnosis or condition"},
            {"name": "icd_codes",     "type": "array",  "description": "ICD diagnosis codes if present"},
            {"name": "medications",   "type": "array",  "description": "Prescribed medications"},
            {"name": "dosage",        "type": "array",  "description": "Dosage instructions per medication"},
            {"name": "visit_date",    "type": "string", "description": "Date of the medical visit"},
        ]
    },

}
def get_all_schema_names() -> list[str]:
    """ Return all available schema names """
    return list(SCHEMA_DEFINITIONS.keys())

def get_schema_fields(schema_name: str) -> list[str] | None:
    """
    Return just the field names for a schema.
    Used by the extraction engine.
    Returns None if schema not found.
    """
    schema = SCHEMA_DEFINITIONS.get(schema_name)
    if not schema:
        return None
    return [field["name"] for field in schema["fields"]]

def get_schema_definition(schema_name: str) -> dict | None:
    """
    Return the full schema definition including field types and descriptions.
    Used by GET /schema/{type} endpoint.
    Returns None if schema not found.
    """
    schema = SCHEMA_DEFINITIONS.get(schema_name.lower())
    if not schema:
        return None

    return {
        "schema":       schema_name.lower(),
        "display_name": schema["display_name"],
        "description":  schema["description"],
        "version":      "1.0",
        "field_count":  len(schema["fields"]),
        "fields":       schema["fields"],
    }

def get_all_schemas_summary() -> list[dict]:
    """"
    Return a Summary of all schemas
    Used by GET /schema to list everything available.
    """
    return [
        {
            "name": name,
            "display_name": definition["display_name"],
            "description": definition["description"],
            "field_count": len(definition["fields"]),
        }
        for name, definition in SCHEMA_DEFINITIONS.items()
    ]


# Database Seeding
async def seed_schemas(db: AsyncSession) -> dict:
    """
    Insert all predefined schemas into the schemas table
    Skips schemas that already exist (safe to run multiple times)
    Returns a summary of what was inserted vs skipped.
    """
    import json as json_lib

    inserted = []
    skipped = []

    for schema_name, definition in SCHEMA_DEFINITIONS.items():
        # Check if this schema already exists
        result = await db.execute(
            select(Schema).where(Schema.name == schema_name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            skipped.append(schema_name)
            continue

        # Insert new schema row
        new_schema = Schema(
            id=uuid.uuid4(),
            name=schema_name,
            display_name=definition["display_name"],
            description=definition["description"],
            fields=definition["fields"],
            version="1.0",
            is_active=True,
        )
        db.add(new_schema)
        inserted.append(schema_name)

    await db.commit()

    return {
        "inserted": inserted,
        "skipped": skipped,
        "total": len(SCHEMA_DEFINITIONS)
    }