from fastapi import APIRouter
from pydantic import BaseModel

from app.crawler.crawler import crawl_site


router = APIRouter(prefix="/crawl", tags=["Crawler"])


class CrawlRequest(BaseModel):
    url: str


@router.post("")
async def crawl(request: CrawlRequest):

    pages = await crawl_site(
        request.url,
        max_pages=5,
    )

    return {
        "start_url": request.url,
        "pages_crawled": len(pages),
        "pages": pages,
    }