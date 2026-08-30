from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.rag.pipeline import answer_question
from app.rag.exceptions import LLMProviderError
from app.repositories.company_repository import get_company_for_user


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    company_id: int
    question: str


@router.post("")
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(
        db=db,
        company_id=request.company_id,
        user_id=current_user.id,
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    try:
        return answer_question(
            question=request.question,
            company_id=company.id,
        )
    except LLMProviderError:
        raise HTTPException(
            status_code=502,
            detail="The language model provider is temporarily unavailable. Please try again.",
        )
