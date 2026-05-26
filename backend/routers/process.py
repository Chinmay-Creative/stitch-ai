from __future__ import annotations

import json
import os
import threading
import time
import uuid

from fastapi import APIRouter, HTTPException

from services import image_processor, region_classifier, vectorizer

job_statuses = {}
job_metadata = {}


def _log_step(job_id: str, step: str, start_time: float) -> float:
    elapsed = time.perf_counter() - start_time
    print(f"Pipeline {job_id}: {step} completed in {elapsed:.2f}s")
    return time.perf_counter()


def run_pipeline(job_id: str):
    try:
        job_statuses[job_id] = "removing_bg"
        validation = image_processor.validate_image(job_id)
        if not validation["valid"]:
            job_statuses[job_id] = "error"
            job_metadata[job_id] = {"error": str(validation.get("issues", "Invalid image"))}
            return

        image_processor.remove_background(job_id)
        job_statuses[job_id] = "enhancing"

        image_processor.enhance_image(job_id)
        job_statuses[job_id] = "vectorizing"

        try:
            vectorizer.vectorize_image(job_id)
        except Exception as e:
            print(f"Vectorization warning: {e}")

        job_statuses[job_id] = "analyzing"

        from services.stitch_engine import generate_contour_stitch_preview, run_full_detection

        regions = run_full_detection(job_id)
        job_statuses[job_id] = "classifying"

        job_statuses[job_id] = "optimizing"

        job_statuses[job_id] = "generating_preview"
        try:
            generate_contour_stitch_preview(job_id)
        except Exception as e:
            print(f"Preview generation warning: {e}")

        job_statuses[job_id] = "complete"
        job_metadata[job_id] = {
            "region_count": len(regions),
            "stitch_types": list(set(r.get("stitch_type", "fill_stitch") for r in regions)),
        }
        print(f"Pipeline complete for {job_id}: {len(regions)} regions")

    except Exception as e:
        job_statuses[job_id] = "error"
        job_metadata[job_id] = {"error": str(e)}
        import traceback

        traceback.print_exc()


router = APIRouter()


@router.post("/api/process")
def start_process(body: dict):
    job_id = body.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id required")
    job_statuses[job_id] = "starting"
    thread = threading.Thread(target=run_pipeline, args=(job_id,))
    thread.daemon = True
    thread.start()
    return {"job_id": job_id, "status": "processing"}


@router.get("/api/status/{job_id}")
def get_status(job_id: str):
    status = job_statuses.get(job_id, "not_found")
    meta = job_metadata.get(job_id, {})
    return {"job_id": job_id, "status": status, **meta}
