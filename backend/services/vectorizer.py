from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET


def vectorize_image(job_id: str) -> str:
    import vtracer

    input_path = os.path.join("uploads", job_id, "enhanced.png")
    output_path = os.path.join("uploads", job_id, "vectorized.svg")

    vtracer.convert_image_to_svg_py(
        input_path,
        output_path,
        colormode="color",
        hierarchical="stacked",
        filter_speckle=4,
        color_precision=8,
        layer_difference=16,
        corner_threshold=60,
        length_threshold=4.0,
        splice_threshold=45,
        path_precision=3,
    )

    return output_path


def _extract_fill_color(path_element: ET.Element) -> str:
    fill = path_element.attrib.get("fill")
    if fill:
        return fill

    style = path_element.attrib.get("style", "")
    for part in style.split(";"):
        key, _, value = part.partition(":")
        if key.strip() == "fill" and value.strip():
            return value.strip()

    return "#000000"


def _estimate_region_size(path_data: str) -> tuple[float, float, float]:
    values = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", path_data)]
    x_values = values[0::2]
    y_values = values[1::2]

    if not x_values or not y_values:
        return 0.0, 0.0, 0.0

    width_mm = (max(x_values) - min(x_values)) / 11.81
    height_mm = (max(y_values) - min(y_values)) / 11.81
    area_mm2 = width_mm * height_mm
    return width_mm, height_mm, area_mm2


def parse_svg_regions(job_id: str) -> list:
    svg_path = os.path.join("uploads", job_id, "vectorized.svg")
    if not os.path.exists(svg_path):
        return []

    tree = ET.parse(svg_path)
    root = tree.getroot()
    ns = {"svg": "http://www.w3.org/2000/svg"}
    regions = []

    for i, element in enumerate(root.iter()):
        tag = element.tag
        if tag.endswith("path") or tag.endswith("rect") or tag.endswith("polygon"):
            fill = _extract_fill_color(element)
            style = element.attrib.get("style", "")
            if "fill:" in style:
                fill_match = re.search(r"fill:\s*(#[0-9a-fA-F]+|rgb[^;]+)", style)
                if fill_match:
                    fill = fill_match.group(1)
            if not fill or fill == "none":
                fill = "#000000"

            d = element.attrib.get("d", "")
            if tag.endswith("rect"):
                x = float(element.attrib.get("x", 0))
                y = float(element.attrib.get("y", 0))
                w = float(element.attrib.get("width", 0))
                h = float(element.attrib.get("height", 0))
                numbers = [x, y, x + w, y + h]
            elif tag.endswith("polygon"):
                points = element.attrib.get("points", "")
                numbers = [float(n) for n in re.findall(r"[-+]?[0-9]*\.?[0-9]+", points)]
            else:
                numbers = [float(n) for n in re.findall(r"[-+]?[0-9]*\.?[0-9]+", d)]

            if len(numbers) >= 4:
                coords_x = [float(numbers[j]) for j in range(0, len(numbers) - 1, 2)]
                coords_y = [float(numbers[j]) for j in range(1, len(numbers), 2)]
                if coords_x and coords_y:
                    min_x, max_x = min(coords_x), max(coords_x)
                    min_y, max_y = min(coords_y), max(coords_y)
                    w = max(max_x - min_x, 5)
                    h = max(max_y - min_y, 5)
                    width_mm = w / 11.81
                    height_mm = h / 11.81
                    area_mm2 = width_mm * height_mm
                    regions.append(
                        {
                            "id": i,
                            "fill_color": fill,
                            "width_mm": round(width_mm, 2),
                            "height_mm": round(height_mm, 2),
                            "area_mm2": round(area_mm2, 2),
                            "bbox": {"x": min_x, "y": min_y, "w": w, "h": h},
                        }
                    )

    if not regions:
        regions = [
            {
                "id": 0,
                "fill_color": "#000000",
                "width_mm": 30,
                "height_mm": 30,
                "area_mm2": 900,
                "bbox": {"x": 50, "y": 50, "w": 300, "h": 300},
            }
        ]

    print(f"Parsed {len(regions)} regions from SVG")
    return regions
