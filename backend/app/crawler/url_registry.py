from typing import Optional

from sqlalchemy.orm import Session

from app.models.url import URLRecord, URLStatus
from app.models.url_db import URL


class URLRegistry:
    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id

    def add(
        self,
        url: str,
        status: URLStatus = URLStatus.DISCOVERED,
        depth: int = 0,
        discovered_from: Optional[str] = None,
    ) -> URLRecord:

        record = (
            self.db.query(URL)
            .filter(
                URL.company_id == self.company_id,
                URL.normalized_url == url,
            )
            .first()
        )

        if record:
            return self._to_record(record)

        record = URL(
            company_id=self.company_id,
            url=url,
            normalized_url=url,
            status=status.value,
            depth=depth,
            discovered_from=discovered_from,
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return self._to_record(record)

    def get(self, url: str) -> Optional[URLRecord]:

        record = (
            self.db.query(URL)
            .filter(
                URL.company_id == self.company_id,
                URL.normalized_url == url,
            )
            .first()
        )

        if not record:
            return None

        return self._to_record(record)

    def update_status(
        self,
        url: str,
        status: URLStatus,
        error: Optional[str] = None,
    ) -> None:

        record = (
            self.db.query(URL)
            .filter(
                URL.company_id == self.company_id,
                URL.normalized_url == url,
            )
            .first()
        )

        if not record:
            return

        record.status = status.value
        record.last_error = error

        self.db.commit()

    def all(self) -> list[URLRecord]:

        records = (
            self.db.query(URL)
            .filter(URL.company_id == self.company_id)
            .all()
        )

        return [
            self._to_record(record)
            for record in records
        ]

    def count(self) -> int:

        return (
            self.db.query(URL)
            .filter(URL.company_id == self.company_id)
            .count()
        )

    @staticmethod
    def _to_record(record: URL) -> URLRecord:

        return URLRecord(
            url=record.url,
            status=URLStatus(record.status),
            depth=record.depth,
            discovered_from=record.discovered_from,
            error=record.last_error,
        )