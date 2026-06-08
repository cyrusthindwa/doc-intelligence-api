import json
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialise the Anthropic client once at module level
# It reads anthropic key from environment automatically
client = anthropic.Anthropic()

# The Claude model to use
MODEL = "claude-opus-4-5"

# Maximum tokens Claude can return
MAX_TOKENS = 1048


def build_text_prompt(doc_text: str, fields: list[str]) -> str:
    """
    Build the extraction prompt for text-based docmunets.
    The prompt is the most important part - it controls what claude returns
    """ 
    fields_list = "\n".join(f"- {field}" for field in fields)
    
    return f"""You are a document data extraction engine.

Extract the following fields from the document text below.

FIELDS TO EXTRACT:
{fields_list}

RULES:
1. Return ONLY a valid JSON object. No explanation, no markdown, no code blocks.
2. Use exactly the field names listed above as JSON keys.
3. If a field cannot be found in the document, set its value to null.
4. For dates, use the format found in the document - do not reformat.
5. For currency amounts, include the currency symbol abd anount as a string.
6. For arrays (e.g. line items, skills), return a JSON array.
7. Do not invent or guess values. Only extract what is explicityly in the document.

DOCUMENT TEXT:
{doc_text}

JSON OUTPUT: """

def build_image_prompt(fields: list[str]) -> str:
    """
    Build the extraction prompt for image-based documents.
    Simpler because the image is passed directly - no text to embed.
    """
    fields_list = "\n".join(f"- {field}" for field in fields)
    
    return f"""You are a document data extraction engine.

Look at this document image and extract the following fields.

FIELDS TO EXTRACT:
{fields_list}

RULES:
1. Return ONLY a valid JSON object. No explanation, no markdown, no code blocks.
2. Use exactly the field names listed above as JSON keys.
3. If a field cannot be found in the image, set its value to null.
4. For dates, use the format shown in the image — do not reformat.
5. For currency amounts, include the currency symbol and amount as a string.
6. For arrays (e.g. line items, skills), return a JSON array.
7. Do not invent or guess values. Only extract what is explicitly visible.

JSON OUTPUT:"""

def clean_json_response(raw_text: str) -> str:
    """
    Claude sometimes wraps JSON in markdown code blocks even when told not to.
    This strips them out so json.loads() can parse cleanly.
    """
    text = raw_text.strip()
    
    # Remove ```json ... ```wrapper
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.startswith("```"):
        text = text[:-3]
        
    return text.strip()

def extract_fields_from_text(doc_text: str, fields: list[str]) -> dict:
    """
    Send document text + field list to Claude.
    Returns extracted fields as a Python dict.
    """
    prompt = build_text_prompt(doc_text,fields)
    
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {
                    "role":"user",
                    "content": prompt
                }
            ]
        )
        
        # Pull the raw text out of Claude's response
        raw_text = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        
        # Clean and parse the JSON
        cleaned = clean_json_response(raw_text)
        
        try:
            extracted = json.loads(cleaned)
        except json.JSONDecodeError:
            # Claide return something that is not valid JSON
            # Return null for all requested fields rather than crashing
            extracted = {field: None for field in fields}
            
        return {
            "success": True,
            "extracted_fields": extracted,
            "tokens_used": tokens_used,
            "raw_response": raw_text,
            "error": None,
        }
        
    except anthropic.AuthenticationError:
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": "INVALID_API_KEY: Check your ANTHROPIC_API_KEY in .env",
        }

    except anthropic.RateLimitError:
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": "RATE_LIMIT: Anthropic API rate limit exceeded. Retry shortly.",
        }

    except anthropic.APIError as e:
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": f"API_ERROR: {str(e)}",
        }

    except Exception as e:
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": f"EXTRACTION_FAILED: {str(e)}",
        }


def extract_fields_from_image(
    base64_data: str,
    mime_type: str,
    fields: list[str]
) -> dict:
    """
    Send a base64-encoded image to Claude vision.
    Claude reads the image directly — no text extraction needed.
    """
    prompt = build_image_prompt(fields)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        # Image block — Claude vision reads this
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": base64_data,
                            }
                        },
                        # Text block — the instructions
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        raw_text = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        cleaned = clean_json_response(raw_text)

        try:
            extracted = json.loads(cleaned)
        except json.JSONDecodeError:
            extracted = {field: None for field in fields}

        return {
            "success": True,
            "extracted_fields": extracted,
            "tokens_used": tokens_used,
            "raw_response": raw_text,
            "error": None,
        }

    except anthropic.AuthenticationError:
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": "INVALID_API_KEY: Check your ANTHROPIC_API_KEY in .env",
        }

    except anthropic.RateLimitError:
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": "RATE_LIMIT: Anthropic API rate limit exceeded. Retry shortly.",
        }

    except anthropic.APIError as e:
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": f"API_ERROR: {str(e)}",
        }

    except Exception as e:
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": f"EXTRACTION_FAILED: {str(e)}",
        }
        
def extract(parsed_document: dict, fields: list[str]) -> dict:
    """
    Master function - receives the output of the parser_router.parse_documents()
    and routes to the correct extraction method.
    
    This is what your FASTAPI routes will call
    """
    if not parsed_document.get("success"):
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": parsed_document.get("error", "PARSE_FAILED: Document could not be parsed"),
        }
        
    input_type = parsed_document.get("input_type")
    
    # Images and scanned PDFs go to Claude vision
    if input_type in ("image", "scanned_pdf"):
        return extract_fields_from_image(
            base64_data=parsed_document["base64_data"],
            mime_type=parsed_document["mime_type"],
            fields=fields,
        )
        
    # Everything else has text - send as text prompt
    doc_text = parsed_document.get("text", "")
    
    if not doc_text or not doc_text.strip():
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": "EMPTY_DOCUMENT: No text content found to extract from",
        }
    return extract_fields_from_text(doc_text,fields)