"""
Storage Utility
===============

Handles file uploads for local storage.

Design Goals:
-------------
• Auto-create directories
• Unique file naming
• Safe file writing
• Reusable across modules (brand, product, user, etc.)

NOTE:
-----
Replace with S3 / Cloudinary in production.
"""

import os
import shutil
from uuid import uuid4
from PIL import Image
from rembg import remove

BASE_UPLOAD_DIR = "uploads"


def save_file(file, folder: str, remove_bg: bool = False) -> str | None:
    """
    Save uploaded file with optional background removal.

    Args:
        file: UploadFile
        folder: subfolder (e.g. brands, products)
        remove_bg: apply background removal (for logos)

    Returns:
        Public file URL
    """

    if not file:
        return None

    # --------------------------------------------------
    # BUILD DIRECTORY PATH
    # --------------------------------------------------
    upload_dir = os.path.join(BASE_UPLOAD_DIR, folder)
    os.makedirs(upload_dir, exist_ok=True)

    # --------------------------------------------------
    # GENERATE UNIQUE FILE NAME
    # --------------------------------------------------
    file_name = f"{uuid4()}.png" if remove_bg else f"{uuid4()}.{file.filename.split('.')[-1]}"
    file_path = os.path.join(upload_dir, file_name)

    # --------------------------------------------------
    # PROCESS IMAGE (IF ENABLED)
    # --------------------------------------------------
    if remove_bg:
        try:
            input_image = Image.open(file.file)

            # 🔥 REMOVE BACKGROUND
            output_image = remove(input_image)

            # Save as PNG (supports transparency)
            output_image.save(file_path)

        except Exception as e:
            # Fallback to normal save
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

    else:
        # --------------------------------------------------
        # NORMAL FILE SAVE
        # --------------------------------------------------
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    # --------------------------------------------------
    # RETURN PUBLIC URL
    # --------------------------------------------------
    return f"/{upload_dir}/{file_name}"