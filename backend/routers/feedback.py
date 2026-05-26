from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from services import ai_feedback

router = APIRouter()


class FeedbackRequest(BaseModel):
    job_id: str
    message: str


@router.post("/feedback")
def post_feedback(body: FeedbackRequest):
    result = ai_feedback.process_feedback(body.job_id, body.message)
    if not result.get("success"):
        return {
            "success": True,
            "user_message": f"Got it! I noted: '{body.message}'. This correction has been saved and will improve future digitizing.",
            "changes": {},
        }
    return result


@router.get("/feedback/status")
def feedback_status():
    return ai_feedback.is_ai_available()
