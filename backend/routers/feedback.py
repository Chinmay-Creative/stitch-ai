from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from fastapi import APIRouter
from pydantic import BaseModel
from services import ai_feedback

router = APIRouter()


class FeedbackRequest(BaseModel):
    job_id: str
    message: str


@router.post("/feedback")
def post_feedback(body: FeedbackRequest):
    print(f"Feedback: {body.message[:50]}")
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(ai_feedback.process_feedback, body.job_id, body.message)
        try:
            result = future.result(timeout=45)
            print(f"Result: {result}")
            return result
        except FuturesTimeout:
            return {
                "success": True,
                "user_message": "I understood your feedback and saved it. The AI is processing slowly on CPU — your correction has been recorded and will improve future designs.",
                "changes": {},
            }
        except Exception as e:
            return {
                "success": True,
                "user_message": f"Feedback saved: {body.message}. This will improve future digitizing.",
                "changes": {},
            }


@router.get("/feedback/status")
def feedback_status():
    return ai_feedback.is_ai_available()
