from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from services import embroidery_generator

router = APIRouter()


@router.get("/export/{job_id}/info")
def export_info(job_id: str):
    import json
    import os

    stitch_estimate = 0
    regions_path = f"uploads/{job_id}/final_regions.json"
    if os.path.exists(regions_path):
        with open(regions_path) as f:
            regions = json.load(f)
        for r in regions:
            stitch_type = r.get("stitch_type", "fill_stitch")
            w = r.get("width_mm", 5)
            h = r.get("height_mm", 5)
            density = r.get("density", 4)
            if stitch_type == "running_stitch":
                stitch_estimate += int((w * h) / 2)
            elif stitch_type == "satin_stitch":
                stitch_estimate += int((w * h) * density / 2)
            else:
                stitch_estimate += int((w * h) * density)

    dst_info = {"valid": os.path.exists(f"outputs/{job_id}/design.dst")}
    pes_info = {"valid": os.path.exists(f"outputs/{job_id}/design.pes")}
    return {
        "dst": dst_info,
        "pes": pes_info,
        "stitch_estimate": stitch_estimate,
        "regions_exist": os.path.exists(regions_path),
    }


@router.get("/export/{job_id}/{format}")
def export_file(job_id: str, format: str):
    import traceback

    if format not in ["dst", "pes"]:
        raise HTTPException(status_code=400, detail="Format must be dst or pes")

    output_path = f"outputs/{job_id}/design.{format}"

    if not os.path.exists(output_path):
        try:
            embroidery_generator.generate_embroidery_file(job_id, format)
        except FileNotFoundError:
            print(f"[EXPORT] No regions found for job {job_id}")
            raise HTTPException(status_code=404, detail="Design not processed yet")
        except Exception as e:
            print(f"[EXPORT] Error generating {format} for {job_id}: {str(e)}")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    if not os.path.exists(output_path):
        print(f"[EXPORT] File {output_path} does not exist after generation attempt")
        raise HTTPException(status_code=500, detail="File generation failed silently")

    return FileResponse(
        path=output_path,
        filename=f"stitchai_design.{format}",
        media_type="application/octet-stream",
    )
