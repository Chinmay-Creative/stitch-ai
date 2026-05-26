from __future__ import annotations

import os
import shutil
import uuid

from fastapi import APIRouter

router = APIRouter()

DESIGNS = [
    {"name": "star", "label": "Simple Star", "description": "Tests fill and outline stitches"},
    {"name": "text", "label": "Hello Text", "description": "Tests text satin stitch"},
    {"name": "circle", "label": "Circle Shape", "description": "Tests circular fill regions"},
]


@router.get("/api/demo/designs")
def get_demo_designs():
    return DESIGNS


@router.post("/api/demo/run/{design_name}")
def run_demo(design_name: str):
    src = f"demo_images/{design_name}.png"
    if not os.path.exists(src):
        return {"error": "Demo image not found"}
    job_id = str(uuid.uuid4())
    os.makedirs(f"uploads/{job_id}", exist_ok=True)
    shutil.copy(src, f"uploads/{job_id}/original.png")
    return {"job_id": job_id}
