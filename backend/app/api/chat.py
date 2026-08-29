from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.rag.pipeline import answer_question


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
    company = (
        db.query(Company)
        .filter(
            Company.id == request.company_id,
            Company.owner_id == current_user.id,
        )
        .first()
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    return answer_question(
        question=request.question,
        company_id=company.id,
    )