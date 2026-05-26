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
        alpha = img[:, :, 3]
    else:
        bgr = img.copy()
        alpha = None

    bgr_masked = cv2.bitwise_and(bgr, bgr, mask=mask)
    hsv = cv2.cvtColor(bgr_masked, cv2.COLOR_BGR2HSV)

    def _cluster_regions(target_mask: np.ndarray) -> list:
        pixel_data = hsv[target_mask > 0]
        if pixel_data.size == 0:
            return []

        pixel_float = pixel_data.astype(np.float32)
        unique_color_count = len(np.unique(pixel_data[:, :2], axis=0))
        if unique_color_count <= 3:
            k = 3
        elif np.mean(pixel_data[:, 1]) < 30:
            k = 2
        else:
            k = min(8, max(2, len(pixel_float) // 1000))

        k = min(k, len(pixel_float))
        if k < 1:
            return []

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        try:
            _, labels, centers = cv2.kmeans(
                pixel_float, k, None, criteria, 3, cv2.KMEANS_RANDOM_CENTERS
            )
        except Exception:
            return []

        regions = []
        label_map = np.zeros(target_mask.shape, dtype=np.int32)
        label_map[target_mask > 0] = labels.flatten() + 1

        for i in range(k):
            region_mask = (label_map == i + 1).astype(np.uint8) * 255
            area = cv2.countNonZero(region_mask)
            if area < 1000:
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
                if cnt_area < 1000:
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

        return regions

    if alpha is not None:
        _, alpha_labels, _, _ = cv2.connectedComponentsWithStats(
            cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)[1], 8, cv2.CV_32S
        )
        alpha_regions = np.unique(alpha_labels[mask > 0])
        if len(alpha_regions) > 2:
            regions = []
            for alpha_label in alpha_regions:
                if alpha_label == 0:
                    continue
                cluster_mask = np.where(alpha_labels == alpha_label, 255, 0).astype(np.uint8)
                cluster_mask = cv2.bitwise_and(cluster_mask, mask)
                if cv2.countNonZero(cluster_mask) < 1000:
                    continue
                regions.extend(_cluster_regions(cluster_mask))
            if regions:
                regions.sort(key=lambda r: r["area_mm2"], reverse=True)
                print(f"Detected {len(regions)} color regions")
                return regions

    regions = _cluster_regions(mask)
    regions.sort(key=lambda r: r["area_mm2"], reverse=True)
    print(f"Detected {len(regions)} color regions")
    return regions


def calculate_region_angle(contour_points: list) -> float:
    import numpy as np

    if not contour_points or len(contour_points) < 5:
        return 0.0

    pts = np.array(contour_points, dtype=np.float32)
    if pts.ndim == 3:
        pts = pts.reshape(-1, 2)
    if len(pts) < 5:
        return 0.0

    try:
        (_, _), (_, _), angle = cv2.fitEllipse(pts.reshape(-1, 1, 2).astype(np.float32))
        return float(angle)
    except Exception:
        rect = cv2.minAreaRect(pts.reshape(-1, 1, 2).astype(np.float32))
        return float(rect[2])


def generate_satin_stitch_lines(contour_mask: np.ndarray, angle_deg: float, density: int) -> list:
    import numpy as np

    h, w = contour_mask.shape
    spacing = max(2, int(8 / density))
    center = (w // 2, h // 2)
    angle_rad = np.radians(angle_deg)
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
    lines = []

    limit = max(h, w)
    for offset in range(-limit, limit, spacing):
        line_points = []
        for t in range(-limit, limit):
            x = int(center[0] + t * cos_a + offset * (-sin_a))
            y = int(center[1] + t * sin_a + offset * cos_a)
            if 0 <= x < w and 0 <= y < h and contour_mask[y, x] > 0:
                line_points.append((x, y))
        if len(line_points) > 2:
            lines.append((line_points[0], line_points[-1]))
    return lines


def generate_underlay(contour_mask: np.ndarray) -> list:
    import numpy as np

    h, w = contour_mask.shape
    underlay_lines = []
    for y in range(0, h, 15):
        row = contour_mask[y, :]
        active = np.where(row > 0)[0]
        if len(active) >= 2:
            underlay_lines.append(((int(active[0]), y), (int(active[-1]), y)))
    return underlay_lines


def generate_fill_with_edge_walk(contour_mask: np.ndarray, density: int) -> list:
    import numpy as np

    h, w = contour_mask.shape
    spacing = max(3, int(10 / density))
    stitches = []
    contours, _ = cv2.findContours(contour_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        edge_points = contours[0].reshape(-1, 2).tolist()
        if len(edge_points) > 4:
            step = max(1, len(edge_points) // 20)
            for i in range(0, len(edge_points), step):
                stitches.append(("edge", tuple(edge_points[i])))

    left_to_right = True
    for y in range(0, h, spacing):
        row = contour_mask[y, :]
        active = np.where(row > 0)[0]
        if len(active) < 2:
            continue
        segments = []
        seg_start = active[0]
        for j in range(1, len(active)):
            if active[j] - active[j - 1] > 5:
                segments.append((seg_start, active[j - 1]))
                seg_start = active[j]
        segments.append((seg_start, active[-1]))
        for x1, x2 in segments:
            if left_to_right:
                stitches.append(("fill", (int(x1), y)))
                stitches.append(("fill", (int(x2), y)))
            else:
                stitches.append(("fill", (int(x2), y)))
                stitches.append(("fill", (int(x1), y)))
        left_to_right = not left_to_right
    return stitches


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
        local_mask = region_mask[y : y + bh, x : x + bw]
        if cv2.countNonZero(local_mask) == 0:
            continue

        color = region.get("fill_color", "#6366f1")
        try:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
        except Exception:
            r, g, b = 99, 102, 241

        stitch_type = region.get("stitch_type", "fill_stitch")
        density = region.get("density", 4)

        if region.get("underlay", False):
            for start, end in generate_underlay(local_mask):
                draw.line(
                    [(x + start[0], y + start[1]), (x + end[0], y + end[1])],
                    fill=(max(0, r - 40), max(0, g - 40), max(0, b - 40), 140),
                    width=1,
                )

        if stitch_type == "running_stitch":
            if contour_data:
                contour_np = np.array(contour_data, dtype=np.int32)
                if contour_np.ndim == 3:
                    contour_np = contour_np.reshape(-1, 2)
                if contour_np.size > 0:
                    for i in range(len(contour_np)):
                        p0 = contour_np[i]
                        p1 = contour_np[(i + 1) % len(contour_np)]
                        dx = int(p1[0] - p0[0])
                        dy = int(p1[1] - p0[1])
                        dist = int(math.hypot(dx, dy))
                        if dist == 0:
                            continue
                        for j in range(0, dist, 8):
                            t = j / max(dist, 1)
                            px = int(p0[0] + dx * t)
                            py = int(p0[1] + dy * t)
                            draw.point((px, py), fill=(r, g, b, 200))
            else:
                for ly in range(y, y + bh, 8):
                    row_pixels = region_mask[ly, x : x + bw]
                    active = np.where(row_pixels > 0)[0]
                    if len(active) < 2:
                        continue
                    draw.line(
                        [(x + active[0], ly), (x + active[-1], ly)],
                        fill=(r, g, b, 180),
                        width=1,
                    )
        elif stitch_type == "satin_stitch":
            angle = calculate_region_angle(contour_data)
            lines = generate_satin_stitch_lines(local_mask, angle, density)
            for start, end in lines:
                draw.line(
                    [(x + start[0], y + start[1]), (x + end[0], y + end[1])],
                    fill=(r, g, b, 160),
                    width=1,
                )
        else:
            stitches = generate_fill_with_edge_walk(local_mask, density)
            for kind, coord in stitches:
                draw.point(
                    (x + coord[0], y + coord[1]),
                    fill=(
                        max(0, r - 40),
                        max(0, g - 40),
                        max(0, b - 40),
                        190,
                    )
                    if kind == "edge"
                    else (r, g, b, 160),
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
