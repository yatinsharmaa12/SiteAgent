from typing import Optional

from app.models.url import URLRecord, URLStatus


class URLRegistry:
    def __init__(self):
        self._urls: dict[str, URLRecord] = {}

    def add(
        self,
        url: str,
        status: URLStatus = URLStatus.DISCOVERED,
        depth: int = 0,
        discovered_from: Optional[str] = None,
    ) -> URLRecord:

        if url in self._urls:
            return self._urls[url]

        record = URLRecord(
            url=url,
            status=status,
            depth=depth,
            discovered_from=discovered_from,
        )

        self._urls[url] = record

        return record

    def get(self, url: str) -> Optional[URLRecord]:
        return self._urls.get(url)

    def update_status(
        self,
        url: str,
        status: URLStatus,
        error: Optional[str] = None,
    ) -> None:

        record = self._urls.get(url)

        if not record:
            return

        record.status = status
        record.error = error

    def all(self) -> list[URLRecord]:
        return list(self._urls.values())

    def count(self) -> int:
        return len(self._urls)