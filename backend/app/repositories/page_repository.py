from typing import Optional

from sqlalchemy.orm import Session

from app.core.time import now_utc_naive
from app.models.page_db import Page


class PageRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_url(
        self,
        company_id: int,
        url_id: int,
    ) -> Optional[Page]:

        return (
            self.db.query(Page)
            .filter(
                Page.company_id == company_id,
                Page.url_id == url_id,
            )
            .first()
        )

    def create(
        self,
        company_id: int,
        url_id: int,
        url: str,
        title: str,
        content: str,
        http_status: Optional[int],
        content_hash: str,
        commit: bool = True,
    ) -> Page:

        page = Page(
            company_id=company_id,
            url_id=url_id,
            url=url,
            title=title,
            content=content,
            http_status=http_status,
            content_hash=content_hash,
            crawled_at=now_utc_naive(),
        )

        self.db.add(page)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        self.db.refresh(page)

        return page

    def update(
        self,
        page: Page,
        title: str,
        content: str,
        http_status: Optional[int],
        content_hash: str,
        commit: bool = True,
    ) -> Page:

        page.title = title
        page.content = content
        page.http_status = http_status
        page.content_hash = content_hash
        page.crawled_at = now_utc_naive()

        if commit:
            self.db.commit()
        else:
            self.db.flush()
        self.db.refresh(page)

        return page
