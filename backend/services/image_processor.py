from __future__ import annotations

import io
import os
from pathlib import Path

import cv2
import numpy as np
import rembg
from PIL import Image, ImageEnhance


def _job_dir(job_id: str) -> Path:
    return Path("uploads") / job_id


def _find_original(job_id: str) -> Path:
    job_dir = _job_dir(job_id)
    matches = sorted(job_dir.glob("original.*"))
    if not matches:
        raise FileNotFoundError(f"No original image found in {job_dir}")
    return matches[0]


def remove_background(job_id: str) -> str:
    original_path = _find_original(job_id)
    output_path = _job_dir(job_id) / "no_bg.png"

    with Image.open(original_path) as img:
        img = img.convert("RGBA")
        input_buffer = io.BytesIO()
        img.save(input_buffer, format="PNG")

    output_bytes = rembg.remove(input_buffer.getvalue())
    output_path.write_bytes(output_bytes)
    return str(output_path)


def enhance_image(job_id: str) -> str:
    input_path = _job_dir(job_id) / "no_bg.png"
    output_path = _job_dir(job_id) / "enhanced.png"

    with Image.open(input_path) as img:
        img = img.convert("RGBA")
        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Sharpness(img).enhance(1.5)
        image_array = np.array(img)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opened = cv2.morphologyEx(image_array, cv2.MORPH_OPEN, kernel)
    enhanced = Image.fromarray(opened)
    enhanced.save(output_path)
    return str(output_path)


def validate_image(job_id: str) -> dict:
    original_path = _find_original(job_id)
    issues = []
    size_bytes = os.path.getsize(original_path)

    with Image.open(original_path) as img:
        width, height = img.size

    if width < 100 or height < 100:
        issues.append("Image dimensions must be at least 100x100 pixels")
    if width > 5000 or height > 5000:
        issues.append("Image dimensions must be no larger than 5000x5000 pixels")
    if size_bytes > 10 * 1024 * 1024:
        issues.append("Image file size must be 10MB or less")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "width": int(width),
        "height": int(height),
    }


def get_image_info(job_id: str) -> dict:
    image_path = _job_dir(job_id) / "enhanced.png"
    size_kb = os.path.getsize(image_path) // 1024

    with Image.open(image_path) as img:
        width, height = img.size

    return {"width": int(width), "height": int(height), "size_kb": int(size_kb)}
