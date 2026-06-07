import base64
import io
import os
from PIL import Image


# Supoorted image types
SUPPORTED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp"}
MAX_IMAGE_SIZE_MB = 10
MAX_IMAGE_DIMENSION = 4096 # pixels - Claude vision limit

def validate_and_prepare_image(file_bytes: bytes, mime_type:str) -> dict:
    """
    Validate an image and prepare it as base64 for Claude vision API.
    Claude vision accepts base64-encoded images directly -  no text extraction needed.
    """
    try:
        # Check MIME type is supported
        if mime_type not in SUPPORTED_MIME_TYPES:
            return {
                "success": False,
                "base64_data": None,
                "mime_type": None,
                "width": None,
                "height": None,
                "error": f"UNSUPPORTED_IMAGE_TYPE: {mime_type}. Supported: PNG, JPEG, WEBP,"
            }
            
        # Check file size
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > MAX_IMAGE_SIZE_MB:
            return {
                "success": False,
                "base64_data": None,
                "mime_type": None,
                "width": None,
                "height": None,
                "error": f"IMAGE_TOO_LARGE: {size_mb:.2f} MB exceeds {MAX_IMAGE_SIZE_MB} MB limit."
            }
            
        # Open with Pillow to validate it is a real image
        image = Image.open(io.BytesIO(file_bytes))
        width,height = image.size
        
        # Resize if image exceeds Claude's dimension limit
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            image.thumbnail(
                (MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION),
                Image.Resampling.LANCZOS
            )
            # Re-encode resized image back to bytes
            buffer = io.BytesIO()
            fmt = "PNG" if mime_type == "image/png" else "JPEG"
            image.save(buffer, format=fmt)
            file_bytes = buffer.getvalue()
            width, height = image.size

        # Encode to base64 - this is the format Claude vision expects
        base64_data = base64.b64encode(file_bytes).decode("utf-8")
        
        # Normalize mime type
        normalized_mime = "image/jpeg" if mime_type == "image/jpg" else mime_type
        
        return {
            "success": True,
            "base64_data": base64_data,
            "mime_type": normalized_mime,
            "width": width,
            "height": height,
            "error": None,
        }
        
    except Exception as e:
        return {
            "success": False,
            "base64_data": None,
            "mime_type": None,
            "width": None,
            "height": None,
            "error": f"IMAGE_VALIDATION_ERROR: {str(e)}",
        }
        
def get_image_info(file_bytes: bytes) -> dict:
    """
    Get basic info about an image without preparing it for Claude
    Useful for logging metadata to the documents table.
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
        
        return {
            "width": image.size[0],
            "height": image.size[1],
            "format": image.format,
            "mode": image.mode,
        }
    
    except Exception as e:
        return {
            "width": None,
            "height": None,
            "format": None,
            "mode": None,
        }