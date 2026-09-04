from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.crawler.ssrf import validate_website_url_syntax
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.repositories.company_repository import (
    get_company_for_user,
    list_companies_for_user,
)


router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


def _validate_website_url(value: str) -> str:
    try:
        return validate_website_url_syntax(value)
    except ValueError as error:
        raise ValueError(str(error))


class CompanyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    website_url: str = Field(min_length=1, max_length=2048)

    @field_validator("website_url")
    @classmethod
    def check_website_url(cls, value: str) -> str:
        return _validate_website_url(value)


class CompanyUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    website_url: str = Field(min_length=1, max_length=2048)

    @field_validator("website_url")
    @classmethod
    def check_website_url(cls, value: str) -> str:
        return _validate_website_url(value)


@router.post("")
def create_company(
    request: CompanyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        website_url = validate_website_url_syntax(request.website_url)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    company = Company(
        name=request.name,
        website_url=website_url,
        owner_id=current_user.id,
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    return {
        "id": company.id,
        "name": company.name,
        "website_url": company.website_url,
    }


@router.get("")
def list_companies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    companies = list_companies_for_user(
        db=db,
        user_id=current_user.id,
    )

    return [
        {
            "id": company.id,
            "name": company.name,
            "website_url": company.website_url,
        }
        for company in companies
    ]


@router.get("/{company_id}")
def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    return {
        "id": company.id,
        "name": company.name,
        "website_url": company.website_url,
    }


@router.put("/{company_id}")
def update_company(
    company_id: int,
    request: CompanyUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    try:
        website_url = validate_website_url_syntax(request.website_url)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    company.name = request.name
    company.website_url = website_url

    db.commit()
    db.refresh(company)

    return {
        "id": company.id,
        "name": company.name,
        "website_url": company.website_url,
    }

@router.delete("/{company_id}")
def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    db.delete(company)
    db.commit()

    return {
        "message": "Company deleted successfully",
        "company_id": company_id,
    }