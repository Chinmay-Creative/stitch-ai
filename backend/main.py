from __future__ import annotations

import os
import traceback
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from routers import admin, export, feedback, process, upload

app = FastAPI(title="StitchAI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (upload.router, feedback.router, export.router, admin.router):
    app.include_router(router, prefix="/api")

app.include_router(process.router)


@app.on_event("startup")
async def create_runtime_folders() -> None:
    for folder in ("uploads", "outputs", "feedback", "ml/training", "demo_images"):
        Path(folder).mkdir(parents=True, exist_ok=True)


@app.get("/api/preview/{job_id}/{image_name}")
def get_preview(job_id: str, image_name: str):
    """Serve preview images (stitch_preview, enhanced, original)."""
    stitch_path = f"uploads/{job_id}/stitch_preview.png"
    if os.path.exists(stitch_path):
        return FileResponse(stitch_path, media_type="image/png")

    for ext in ["png", "jpg", "jpeg"]:
        path = f"uploads/{job_id}/{image_name}.{ext}"
        if os.path.exists(path):
            return FileResponse(path, media_type="image/png")

    raise HTTPException(status_code=404, detail="Preview not found")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": "StitchAI"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url.path),
        },
    )
