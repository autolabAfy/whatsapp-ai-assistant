"""
Image Storage for Property Photos
Handles upload, storage, and retrieval of property images
"""
import os
import uuid
from pathlib import Path
from typing import Optional
from loguru import logger
import base64
from PIL import Image
from io import BytesIO


# Storage directory
UPLOAD_DIR = Path("uploads/properties")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_property_image(
    image_data: str,
    property_id: str,
    image_type: str = "main"
) -> str:
    """
    Save property image from base64 data

    Args:
        image_data: Base64 encoded image or file path
        property_id: UUID of property
        image_type: "main", "thumbnail", "gallery"

    Returns:
        Relative path to saved image
    """
    try:
        # Generate unique filename
        image_id = str(uuid.uuid4())[:8]
        filename = f"{property_id}_{image_type}_{image_id}.jpg"
        filepath = UPLOAD_DIR / filename

        # Decode base64 if needed
        if image_data.startswith('data:image'):
            # Remove data:image/jpeg;base64, prefix
            image_data = image_data.split(',')[1]

        # Decode and save
        image_bytes = base64.b64decode(image_data)

        # Open with PIL to validate and optimize
        img = Image.open(BytesIO(image_bytes))

        # Resize if too large (max 1920x1080)
        max_size = (1920, 1080)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Save as JPEG
        img.save(filepath, "JPEG", quality=85, optimize=True)

        logger.info(f"Saved property image: {filename}")

        # Return relative path
        return f"uploads/properties/{filename}"

    except Exception as e:
        logger.error(f"Failed to save property image: {e}")
        raise


def get_image_url(image_path: str, base_url: str) -> str:
    """
    Convert relative path to full URL

    Args:
        image_path: Relative path (e.g., "uploads/properties/abc.jpg")
        base_url: Base URL of API (e.g., "https://app.railway.app")

    Returns:
        Full URL to image
    """
    if not image_path:
        return None

    return f"{base_url}/{image_path}"


def delete_property_images(property_id: str):
    """
    Delete all images for a property

    Args:
        property_id: UUID of property
    """
    try:
        # Find all images for this property
        pattern = f"{property_id}_*.jpg"
        for image_file in UPLOAD_DIR.glob(pattern):
            image_file.unlink()
            logger.info(f"Deleted image: {image_file.name}")
    except Exception as e:
        logger.error(f"Failed to delete property images: {e}")


def create_thumbnail(image_path: str) -> str:
    """
    Create thumbnail from existing image

    Args:
        image_path: Path to original image

    Returns:
        Path to thumbnail
    """
    try:
        original = Image.open(image_path)

        # Create thumbnail (300x200)
        thumbnail_size = (300, 200)
        original.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

        # Save as thumbnail
        thumb_path = str(image_path).replace('.jpg', '_thumb.jpg')
        original.save(thumb_path, "JPEG", quality=80)

        return thumb_path

    except Exception as e:
        logger.error(f"Failed to create thumbnail: {e}")
        return None


if __name__ == "__main__":
    # Test
    print(f"Upload directory: {UPLOAD_DIR.absolute()}")
    print(f"Upload directory exists: {UPLOAD_DIR.exists()}")
