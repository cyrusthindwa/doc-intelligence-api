import json
import os
from dotenv import load_dotenv

# Only load .env in local dev, not in Docker
if not os.getenv("DOCKER_ENV"):
    load_dotenv()

# ── Provider configuration ────────────────────────────────────
# Set AI_PROVIDER in .env to "groq" or "anthropic" (default)
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic").strip().lower()

# Maximum tokens Claude can return
MAX_TOKENS = 4096


# ── Provider-specific config ──────────────────────────────────
if AI_PROVIDER == "groq":
    from groq import Groq

    MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "llama-3.2-90b-vision-preview")

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def _call_text(prompt: str) -> "tuple[str, int]":
        """Call Groq chat completions for text extraction."""
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0
        return raw, tokens

    def _call_vision(prompt: str, base64_data: str, mime_type: str) -> "tuple[str, int]":
        """Call Groq chat completions with an image for vision extraction."""
        response = client.chat.completions.create(
            model=VISION_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_data}"
                        },
                    },
                ],
            }],
        )
        raw = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0
        return raw, tokens

    # Error mapping for Groq
    _AuthError = Exception  # Groq uses generic exceptions; handled in try/except
    _RateLimitError = Exception

else:
    # Default: Anthropic
    import anthropic

    MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5")
    VISION_MODEL = MODEL  # Anthropic uses the same model for vision

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _call_text(prompt: str) -> "tuple[str, int]":
        """Call Anthropic messages for text extraction."""
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return raw, tokens

    def _call_vision(prompt: str, base64_data: str, mime_type: str) -> "tuple[str, int]":
        """Call Anthropic messages with an image for vision extraction."""
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": base64_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        raw = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return raw, tokens

    _AuthError = anthropic.AuthenticationError
    _RateLimitError = anthropic.RateLimitError


def get_active_model() -> str:
    """Return the model name currently in use (for metadata)."""
    return MODEL


def get_active_provider() -> str:
    """Return the provider name currently in use."""
    return AI_PROVIDER


# ── Prompt builders (provider-agnostic) ────────────────────────

def build_text_prompt(doc_text: str, fields: list[str]) -> str:
    """
    Build the extraction prompt for text-based documents.
    The prompt is the most important part — it controls what the model returns.
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
4. For dates, use the format found in the document — do not reformat.
5. For currency amounts, include the currency symbol and amount as a string.
6. For arrays (e.g. line items, skills), return a JSON array.
7. Do not invent or guess values. Only extract what is explicitly in the document.

DOCUMENT TEXT:
{doc_text}

JSON OUTPUT:"""


def build_image_prompt(fields: list[str]) -> str:
    """
    Build the extraction prompt for image-based documents.
    Simpler because the image is passed directly — no text to embed.
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


# ── JSON cleaner ──────────────────────────────────────────────

def clean_json_response(raw_text: str) -> str:
    """
    Models sometimes wrap JSON in markdown code blocks even when told not to.
    This strips them out so json.loads() can parse cleanly.
    """
    text = raw_text.strip()

    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


# ── Extraction functions ──────────────────────────────────────

def extract_fields_from_text(doc_text: str, fields: list[str]) -> dict:
    """
    Send document text + field list to the configured AI provider.
    Returns extracted fields as a Python dict.
    """
    prompt = build_text_prompt(doc_text, fields)

    try:
        raw_text, tokens_used = _call_text(prompt)
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

    except _AuthError:
        provider_key = "GROQ_API_KEY" if AI_PROVIDER == "groq" else "ANTHROPIC_API_KEY"
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": f"INVALID_API_KEY: Check your {provider_key} in .env",
        }

    except _RateLimitError:
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": f"RATE_LIMIT: {AI_PROVIDER.title()} API rate limit exceeded. Retry shortly.",
        }

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "authentication" in error_msg.lower():
            provider_key = "GROQ_API_KEY" if AI_PROVIDER == "groq" else "ANTHROPIC_API_KEY"
            error_msg = f"INVALID_API_KEY: Check your {provider_key} in .env"

        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": f"API_ERROR: {error_msg}",
        }


def extract_fields_from_image(
    base64_data: str,
    mime_type: str,
    fields: list[str]
) -> dict:
    """
    Send a base64-encoded image to the configured AI provider's vision model.
    """
    prompt = build_image_prompt(fields)

    try:
        raw_text, tokens_used = _call_vision(prompt, base64_data, mime_type)
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

    except _AuthError:
        provider_key = "GROQ_API_KEY" if AI_PROVIDER == "groq" else "ANTHROPIC_API_KEY"
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": f"INVALID_API_KEY: Check your {provider_key} in .env",
        }

    except _RateLimitError:
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": f"RATE_LIMIT: {AI_PROVIDER.title()} API rate limit exceeded. Retry shortly.",
        }

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "authentication" in error_msg.lower():
            provider_key = "GROQ_API_KEY" if AI_PROVIDER == "groq" else "ANTHROPIC_API_KEY"
            error_msg = f"INVALID_API_KEY: Check your {provider_key} in .env"

        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": f"API_ERROR: {error_msg}",
        }


def extract(parsed_document: dict, fields: list[str]) -> dict:
    """
    Master function — receives the output of parser_router.parse_document()
    and routes to the correct extraction method.

    This is what your FastAPI routes will call.
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

    # Images and scanned PDFs go to the vision model
    if input_type in ("image", "scanned_pdf"):
        return extract_fields_from_image(
            base64_data=parsed_document["base64_data"],
            mime_type=parsed_document["mime_type"],
            fields=fields,
        )

    # Everything else has text — send as text prompt
    doc_text = parsed_document.get("text", "")

    if not doc_text or not doc_text.strip():
        return {
            "success": False,
            "extracted_fields": {field: None for field in fields},
            "tokens_used": 0,
            "raw_response": None,
            "error": "EMPTY_DOCUMENT: No text content found to extract from",
        }
    return extract_fields_from_text(doc_text, fields)