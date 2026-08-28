from pydantic import BaseModel


class CrawledPage(BaseModel):
    url: str
    title: str
    content: str
    links: list[str]
    status: str