from __future__ import annotations

import json
import math
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw


def load_image_as_array(job_id: str) -> np.ndarray:
    for name in ["enhanced.png", "no_bg.png", "original.png", "original.jpg"]:
        path = f"uploads/{job_id}/{name}"
        if os.path.exists(path):
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is not None:
                return img
    raise FileNotFoundError(f"No image found for job {job_id}")


def extract_subject_mask(img: np.ndarray) -> np.ndarray:
    if img.shape[2] == 4:
        alpha = img[:, :, 3]
        _, mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask


def detect_color_regions(img: np.ndarray, mask: np.ndarray) -> list:
    if img.shape[2] == 4:
        bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    else:
        bgr = img.copy()

    bgr_masked = cv2.bitwise_and(bgr, bgr, mask=mask)
    hsv = cv2.cvtColor(bgr_masked, cv2.COLOR_BGR2HSV)

    pixel_data = hsv[mask > 0]
    if len(pixel_data) == 0:
        return []

    pixel_float = pixel_data.astype(np.float32)
    k = min(8, max(1, len(pixel_float) // 1000))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)

    try:
        _, labels, centers = cv2.kmeans(
            pixel_float, k, None, criteria, 3, cv2.KMEANS_RANDOM_CENTERS
        )
    except Exception:
        return []

    regions = []
    label_map = np.zeros(mask.shape, dtype=np.int32)
    label_map[mask > 0] = labels.flatten() + 1

    for i in range(k):
        region_mask = (label_map == i + 1).astype(np.uint8) * 255
        area = cv2.countNonZero(region_mask)
        if area < 500:
            continue

        contours, _ = cv2.findContours(region_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue

        hsv_center = centers[i]
        h, s, v = int(hsv_center[0]), int(hsv_center[1]), int(hsv_center[2])
        bgr_color = cv2.cvtColor(np.uint8([[[h, s, v]]]), cv2.COLOR_HSV2BGR)[0][0]
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(bgr_color[2]), int(bgr_color[1]), int(bgr_color[0])
        )

        for contour in contours:
            cnt_area = cv2.contourArea(contour)
            if cnt_area < 200:
                continue
            x, y, w, h_box = cv2.boundingRect(contour)
            width_mm = w / 11.81
            height_mm = h_box / 11.81
            area_mm2 = cnt_area / (11.81**2)

            if width_mm < 2.0:
                stitch_type = "running_stitch"
                density = 3
            elif width_mm < 8.0:
                stitch_type = "satin_stitch"
                density = 5
            else:
                stitch_type = "fill_stitch"
                density = 4

            regions.append(
                {
                    "fill_color": hex_color,
                    "width_mm": round(width_mm, 2),
                    "height_mm": round(height_mm, 2),
                    "area_mm2": round(area_mm2, 2),
                    "stitch_type": stitch_type,
                    "density": density,
                    "underlay": stitch_type != "running_stitch",
                    "contour": contour.tolist(),
                    "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h_box)},
                }
            )

    regions.sort(key=lambda r: r["area_mm2"], reverse=True)
    print(f"Detected {len(regions)} color regions")
    return regions


def generate_contour_stitch_preview(job_id: str) -> str:
    img_array = load_image_as_array(job_id)
    mask = extract_subject_mask(img_array)

    regions_path = f"uploads/{job_id}/final_regions.json"
    if not os.path.exists(regions_path):
        return f"uploads/{job_id}/enhanced.png"

    with open(regions_path) as f:
        regions = json.load(f)

    h, w = img_array.shape[:2]
    if img_array.shape[2] == 4:
        pil_img = Image.fromarray(cv2.cvtColor(img_array, cv2.COLOR_BGRA2RGBA))
    else:
        pil_img = Image.fromarray(cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB))

    white_bg = Image.new("RGB", (w, h), (255, 255, 255))
    if pil_img.mode == "RGBA":
        white_bg.paste(pil_img, mask=pil_img.split()[3])
    else:
        white_bg.paste(pil_img)

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for region in regions:
        contour_data = region.get("contour")
        bbox = region.get("bbox", {})
        if not bbox:
            continue

        x = max(0, int(bbox.get("x", 0)))
        y = max(0, int(bbox.get("y", 0)))
        bw = min(w - x, max(1, int(bbox.get("w", 10))))
        bh = min(h - y, max(1, int(bbox.get("h", 10))))

        if bw < 3 or bh < 3:
            continue

        region_mask = np.zeros((h, w), dtype=np.uint8)
        if contour_data:
            contour_np = np.array(contour_data, dtype=np.int32)
            if contour_np.ndim == 3:
                cv2.fillPoly(region_mask, [contour_np], 255)
            elif contour_np.ndim == 2:
                cv2.fillPoly(region_mask, [contour_np.reshape(-1, 1, 2)], 255)
        else:
            region_mask[y : y + bh, x : x + bw] = 255

        region_mask = cv2.bitwise_and(region_mask, mask)

        color = region.get("fill_color", "#6366f1")
        try:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
        except Exception:
            r, g, b = 99, 102, 241

        stitch_type = region.get("stitch_type", "fill_stitch")
        density = region.get("density", 4)

        if stitch_type == "running_stitch":
            spacing = 8
        elif stitch_type == "satin_stitch":
            spacing = max(2, int(6 / density))
        else:
            spacing = max(3, int(5 / density))

        for ly in range(y, y + bh, spacing):
            row_pixels = region_mask[ly, x : x + bw]
            active = np.where(row_pixels > 0)[0]
            if len(active) == 0:
                continue
            segments = []
            seg_start = active[0]
            for j in range(1, len(active)):
                if active[j] - active[j - 1] > 3:
                    segments.append((seg_start, active[j - 1]))
                    seg_start = active[j]
            segments.append((seg_start, active[-1]))
            for seg_x1, seg_x2 in segments:
                if seg_x2 - seg_x1 > 2:
                    draw.line(
                        [(x + seg_x1, ly), (x + seg_x2, ly)],
                        fill=(r, g, b, 160),
                        width=1,
                    )

    overlay_rgb = Image.new("RGB", (w, h), (255, 255, 255))
    mask_pil = overlay.split()[3]
    overlay_rgb.paste(overlay.convert("RGB"), mask=mask_pil)

    result = Image.blend(white_bg, overlay_rgb, alpha=0.6)
    preview_path = f"uploads/{job_id}/stitch_preview.png"
    result.save(preview_path)
    print(f"Saved contour stitch preview: {preview_path}")
    return preview_path


def run_full_detection(job_id: str) -> list:
    print(f"Running full shape detection for job {job_id}")
    img_array = load_image_as_array(job_id)
    mask = extract_subject_mask(img_array)
    regions = detect_color_regions(img_array, mask)

    if not regions:
        print("No regions detected, using fallback")
        regions = [
            {
                "fill_color": "#000000",
                "width_mm": 30.0,
                "height_mm": 30.0,
                "area_mm2": 900.0,
                "stitch_type": "fill_stitch",
                "density": 4,
                "underlay": True,
                "contour": None,
                "bbox": {"x": 50, "y": 50, "w": 300, "h": 300},
            }
        ]

    output_path = f"uploads/{job_id}/final_regions.json"
    with open(output_path, "w") as f:
        json.dump(regions, f)

    print(f"Saved {len(regions)} regions")
    return regions
