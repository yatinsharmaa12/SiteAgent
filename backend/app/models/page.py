from pydantic import BaseModel

# Re-export ORM Page model for tests
from .page_db import Page


class CrawledPage(BaseModel):
    url: str
    title: str
    content: str
    links: list[str]
    status: str