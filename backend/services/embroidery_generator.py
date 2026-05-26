from __future__ import annotations
"""Embroidery file generator using pyembroidery.

This module is safe to import even if `pyembroidery` is not installed —
real generation functions will raise if the package is missing.
"""
try:
    import pyembroidery
except Exception:  # pragma: no cover - optional dependency
    pyembroidery = None

import json
import math
import os


def pixel_to_units(px: float) -> int:
    """Convert image pixels to pyembroidery 0.1mm units.

    Formula: px * 10 / 11.81
    """
    return int(px * 10 / 11.81)


def generate_running_stitch_coords(region: dict) -> list:
    bbox = region.get("bbox", {})
    x = pixel_to_units(bbox.get("x", 0))
    y = pixel_to_units(bbox.get("y", 0))
    w = pixel_to_units(bbox.get("w", 10))
    h = pixel_to_units(bbox.get("h", 10))
    length = int(region.get("length_mm", 2.0) * 10)
    coords = []
    cx = x
    while cx < x + w:
        coords.append((cx, y))
        coords.append((cx, y + h))
        cx += length
    return coords


def generate_satin_stitch_coords(region: dict) -> list:
    bbox = region.get("bbox", {})
    x = pixel_to_units(bbox.get("x", 0))
    y = pixel_to_units(bbox.get("y", 0))
    w = pixel_to_units(bbox.get("w", 10))
    h = pixel_to_units(bbox.get("h", 10))
    density = region.get("density", 5)
    spacing = max(1, int(10 / density))
    coords = []
    cy = y
    left = True
    while cy < y + h:
        if left:
            coords.append((x, cy))
            coords.append((x + w, cy))
        else:
            coords.append((x + w, cy))
            coords.append((x, cy))
        cy += spacing
        left = not left
    return coords


def generate_fill_stitch_coords(region: dict) -> list:
    bbox = region.get("bbox", {})
    x = pixel_to_units(bbox.get("x", 0))
    y = pixel_to_units(bbox.get("y", 0))
    w = pixel_to_units(bbox.get("w", 10))
    h = pixel_to_units(bbox.get("h", 10))
    row_spacing = int(region.get("row_spacing_mm", 0.4) * 10)
    row_spacing = max(4, row_spacing)
    coords = []
    cy = y
    left = True
    while cy < y + h:
        if left:
            coords.append((x, cy))
            coords.append((x + w, cy))
        else:
            coords.append((x + w, cy))
            coords.append((x, cy))
        cy += row_spacing
        left = not left
    return coords


def add_bbox_to_regions(regions: list, image_width: int, image_height: int) -> list:
    count = len(regions)
    if count == 0:
        return regions

    cols = max(1, int(count**0.5))
    cell_h = image_height / max(1, (count + cols - 1) // cols)

    for i, region in enumerate(regions):
        if "bbox" not in region or not region.get("bbox"):
            width_mm = region.get("width_mm", 10)
            height_mm = region.get("height_mm", 10)
            width_px = width_mm * 11.81
            height_px = height_mm * 11.81
            col = i % cols
            row = i // cols
            cell_w = image_width / cols
            cell_h = image_height / max(1, (count + cols - 1) // cols)
            region["bbox"] = {
                "x": col * cell_w + cell_w * 0.1,
                "y": row * cell_h + cell_h * 0.1,
                "w": min(width_px, cell_w * 0.8),
                "h": min(height_px, cell_h * 0.8),
            }
    return regions


def generate_embroidery_file(job_id: str, format: str) -> str:
    """Generate an embroidery file for a job and return the output path.

    This function requires `pyembroidery` to be installed. If it's missing
    a RuntimeError will be raised when attempting to write the file.
    """
    regions_path = f"uploads/{job_id}/final_regions.json"
    if not os.path.exists(regions_path):
        raise FileNotFoundError(f"No regions found for job {job_id}")

    with open(regions_path) as f:
        regions = json.load(f)

    if not regions:
        regions = [
            {
                "stitch_type": "fill_stitch",
                "fill_color": "#000000",
                "width_mm": 20,
                "height_mm": 20,
                "density": 4,
                "row_spacing_mm": 0.4,
                "bbox": {"x": 50, "y": 50, "w": 200, "h": 200},
            }
        ]

    image_width = 400
    image_height = 400
    enhanced_path = f"uploads/{job_id}/enhanced.png"
    if os.path.exists(enhanced_path):
        try:
            from PIL import Image

            img = Image.open(enhanced_path)
            image_width, image_height = img.size
        except Exception:
            pass

    regions = add_bbox_to_regions(regions, image_width, image_height)

    if pyembroidery is None:
        raise RuntimeError("pyembroidery is not installed; cannot generate files")

    pattern = pyembroidery.EmbPattern()

    color_groups = {}
    for region in regions:
        color = region.get("fill_color", "#000000")
        color_groups.setdefault(color, []).append(region)

    first_color = True
    for color, group in color_groups.items():
        if not first_color:
            pattern.add_command(pyembroidery.COLOR_CHANGE)
        first_color = False

        try:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
        except Exception:
            r, g, b = 0, 0, 0

        pattern.add_thread({"color": (r << 16) | (g << 8) | b, "name": f"Thread_{color}"})

        for region in group:
            stitch_type = region.get("stitch_type", "fill_stitch")
            if stitch_type == "running_stitch":
                coords = generate_running_stitch_coords(region)
            elif stitch_type == "satin_stitch":
                coords = generate_satin_stitch_coords(region)
            else:
                coords = generate_fill_stitch_coords(region)

            for x, y in coords:
                pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)

            pattern.add_command(pyembroidery.TRIM)

    pattern.add_command(pyembroidery.END)

    stitch_count = len(pattern.stitches) if hasattr(pattern, "stitches") else 0
    print(f"Generated {stitch_count} stitches")

    if stitch_count < 10:
        print("WARNING: Too few stitches, adding fallback pattern")
        for y in range(100, 400, 10):
            pattern.add_stitch_absolute(pyembroidery.STITCH, 100, y)
            pattern.add_stitch_absolute(pyembroidery.STITCH, 400, y)
        pattern.add_command(pyembroidery.TRIM)

    os.makedirs(f"outputs/{job_id}", exist_ok=True)
    output_path = f"outputs/{job_id}/design.{format}"
    pyembroidery.write(pattern, output_path)

    if not os.path.exists(output_path):
        raise RuntimeError(f"File generation failed for {output_path}")

    return output_path


def generate_preview_image(job_id: str) -> str:
    from PIL import Image, ImageDraw
    import numpy as np
    import json
    import os

    enhanced_path = f"uploads/{job_id}/enhanced.png"
    regions_path = f"uploads/{job_id}/final_regions.json"

    if not os.path.exists(enhanced_path):
        return enhanced_path

    img = Image.open(enhanced_path).convert("RGBA")
    img_array = np.array(img)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if os.path.exists(regions_path):
        with open(regions_path) as f:
            regions = json.load(f)

        for region in regions:
            bbox = region.get("bbox", {})
            if not bbox:
                continue

            x = max(0, int(bbox.get("x", 0)))
            y = max(0, int(bbox.get("y", 0)))
            w = max(1, int(bbox.get("w", 10)))
            h = max(1, int(bbox.get("h", 10)))

            x2 = min(img.width, x + w)
            y2 = min(img.height, y + h)

            if x >= img.width or y >= img.height or x2 <= x or y2 <= y:
                continue

            region_pixels = img_array[y:y2, x:x2]
            if region_pixels.size == 0:
                continue

            if img_array.shape[2] == 4:
                avg_alpha = region_pixels[:, :, 3].mean()
                if avg_alpha < 30:
                    continue

            avg_r = region_pixels[:, :, 0].mean()
            avg_g = region_pixels[:, :, 1].mean()
            avg_b = region_pixels[:, :, 2].mean()
            if avg_r > 230 and avg_g > 230 and avg_b > 230:
                continue

            stitch_type = region.get("stitch_type", "fill_stitch")
            color = region.get("fill_color", "#6366f1")
            try:
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
            except Exception:
                r, g, b = 99, 102, 241

            if stitch_type == "running_stitch":
                for lx in range(x, x2, 8):
                    draw.line([(lx, y + (y2 - y) // 2), (lx + 4, y + (y2 - y) // 2)], fill=(r, g, b, 180), width=1)
            elif stitch_type == "satin_stitch":
                for ly in range(y, y2, 3):
                    draw.line([(x, ly), (x2, ly)], fill=(r, g, b, 160), width=1)
            else:
                for ly in range(y, y2, 5):
                    if (ly // 5) % 2 == 0:
                        draw.line([(x, ly), (x2, ly)], fill=(r, g, b, 140), width=1)
                    else:
                        draw.line([(x2, ly), (x, ly)], fill=(r, g, b, 140), width=1)

    combined = Image.alpha_composite(img, overlay)
    img_out = Image.new("RGB", img.size, (255, 255, 255))
    img_out.paste(combined, mask=combined.split()[3])
    preview_path = f"uploads/{job_id}/stitch_preview.png"
    img_out.save(preview_path)
    return preview_path


def validate_pattern(job_id: str, format: str) -> dict:
    output_path = f"outputs/{job_id}/design.{format}"
    if not os.path.exists(output_path):
        return {"valid": False, "reason": "File not found"}
    size = os.path.getsize(output_path)
    return {"valid": size > 0, "file_size_bytes": size, "format": format, "path": output_path}
