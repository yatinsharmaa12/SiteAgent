from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.crawler.crawler import crawl_site
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User


router = APIRouter(
    prefix="/crawl",
    tags=["Crawler"],
)


class CrawlRequest(BaseModel):
    url: str

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


@router.post("")
async def crawl(
    request: CrawlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = (
        db.query(Company)
        .filter(
            Company.website_url == request.url,
            Company.owner_id == current_user.id,
        )
        .first()
    )

    if not company:
        company = Company(
            name=request.url,
            website_url=request.url,
            owner_id=current_user.id,
        )

        db.add(company)
        db.commit()
        db.refresh(company)

    pages, registry = await crawl_site(
        request.url,
        db=db,
        company_id=company.id,
        max_pages=request.max_pages,
        max_depth=request.max_depth,
    )

    return {
        "start_url": request.url,
        "company_id": company.id,
        "pages_crawled": len(pages),
        "pages": pages,
        "url_registry": registry.all(),
    }