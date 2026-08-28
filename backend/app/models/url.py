from enum import Enum
from typing import Optional

from pydantic import BaseModel


class URLStatus(str, Enum):
    DISCOVERED = "discovered"
    QUEUED = "queued"
    CRAWLING = "crawling"
    CRAWLED = "crawled"
    INDEXED = "indexed"
    FAILED = "failed"


class URLRecord(BaseModel):
    url: str
    status: URLStatus
    depth: int = 0
    discovered_from: Optional[str] = None
    error: Optional[str] = None