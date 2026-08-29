from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.pipeline import answer_question


router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    question: str


@router.post("")
def chat(request: ChatRequest):
    answer = answer_question(request.question)

    return {
        "answer": answer,
    }