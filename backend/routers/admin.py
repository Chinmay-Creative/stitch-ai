from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["admin"])


@router.get("/admin/training-report")
async def training_report() -> dict[str, int]:
    return {"total_feedback": 0}
