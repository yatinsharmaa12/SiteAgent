from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.page_db import Page


class PageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: int,
        url_id: int,
        url: str,
        title: str,
        content: str,
        http_status: Optional[int],
        content_hash: str,
    ) -> Page:

        page = Page(
            company_id=company_id,
            url_id=url_id,
            url=url,
            title=title,
            content=content,
            http_status=http_status,
            content_hash=content_hash,
            crawled_at=datetime.utcnow(),
        )

        self.db.add(page)
        self.db.commit()
        self.db.refresh(page)

        return page