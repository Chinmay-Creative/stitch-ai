from __future__ import annotations

import json
import os


def classify_region(region: dict) -> dict:
    width = region.get("width_mm", 0)
    if width < 2.0:
        region["stitch_type"] = "running_stitch"
        region["density"] = 3
        region["length_mm"] = 2.0
        region["underlay"] = False
    elif width < 6.0:
        region["stitch_type"] = "satin_stitch"
        region["density"] = 5
        region["underlay"] = True
        region["pull_compensation"] = 0.3
        region["angle"] = 0
    else:
        region["stitch_type"] = "fill_stitch"
        region["density"] = 4
        region["angle"] = 45
        region["row_spacing_mm"] = 0.4
        region["underlay"] = True
        region["edge_walk"] = True
    return region


def load_learned_rules() -> dict:
    try:
        with open(os.path.join("ml", "models", "learned_rules.json")) as f:
            return json.load(f)
    except Exception:
        return {}
