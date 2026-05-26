from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)) -> dict:
    job_id = str(uuid4())
    content = await file.read()
    suffix = Path(file.filename or "upload.png").suffix or ".png"
    job_dir = Path("uploads") / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / f"original{suffix}").write_bytes(content)

    return {
        "job_id": job_id,
        "filename": file.filename or "upload",
        "size": len(content),
    }
