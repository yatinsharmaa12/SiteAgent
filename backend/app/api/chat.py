from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.pipeline import answer_question


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    company_id: int
    question: str


@router.post("")
def chat(request: ChatRequest):
    return answer_question(
        question=request.question,
        company_id=request.company_id,
    )