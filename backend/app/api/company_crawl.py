from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.crawler.crawler import crawl_site
from app.db.session import get_db
from app.models.user import User
from app.repositories.company_repository import get_company_for_user


router = APIRouter(
    prefix="/companies",
    tags=["Company Crawler"],
)


class CrawlCompanyRequest(BaseModel):
    max_pages: int = Field(
        default=5,
        ge=1,
        le=100,
    )

    max_depth: int = Field(
        default=1,
        ge=0,
        le=10,
    )


@router.post("/{company_id}/crawl")
async def crawl_company(
    company_id: int,
    request: CrawlCompanyRequest,
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

    pages, registry = await crawl_site(
        company.website_url,
        db=db,
        company_id=company.id,
        max_pages=request.max_pages,
        max_depth=request.max_depth,
    )

    return {
        "company_id": company.id,
        "company_name": company.name,
        "start_url": company.website_url,
        "pages_crawled": len(pages),
        "pages": pages,
        "url_registry": registry.all(),
    }