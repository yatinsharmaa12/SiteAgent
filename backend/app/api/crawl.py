from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.crawler.crawler import crawl_site
from app.db.session import get_db
from app.models.company import Company


router = APIRouter(prefix="/crawl", tags=["Crawler"])


class CrawlRequest(BaseModel):
    url: str


@router.post("")
async def crawl(
    request: CrawlRequest,
    db: Session = Depends(get_db),
):
    company = (
        db.query(Company)
        .filter(Company.website_url == request.url)
        .first()
    )

    if not company:
        company = Company(
            name=request.url,
            website_url=request.url,
        )

        db.add(company)
        db.commit()
        db.refresh(company)

    pages, registry = await crawl_site(
        request.url,
        db=db,
        company_id=company.id,
        max_pages=5,
        max_depth=1,
    )

    return {
        "start_url": request.url,
        "company_id": company.id,
        "pages_crawled": len(pages),
        "pages": pages,
        "url_registry": registry.all(),
    }