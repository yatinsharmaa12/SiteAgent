from collections import deque
from urllib.parse import urlparse

from app.crawler.fetcher import fetch_page
from app.crawler.parser import parse_page
from app.crawler.link_extractor import extract_links
from app.models.page import CrawledPage
from app.models.url import URLStatus
from app.crawler.url_registry import URLRegistry


async def crawl_site(
    start_url: str,
    max_pages: int = 5,
) -> tuple[list[CrawledPage], URLRegistry]:

    queue = deque([start_url])
    registry = URLRegistry()
    pages = []

    start_domain = urlparse(start_url).hostname

    registry.add(
        start_url,
        status=URLStatus.QUEUED,
        depth=0,
    )

    while queue and len(pages) < max_pages:

        current_url = queue.popleft()

        record = registry.get(current_url)

        if not record:
            continue

        if record.status in {
            URLStatus.CRAWLED,
            URLStatus.INDEXED,
        }:
            continue

        if urlparse(current_url).hostname != start_domain:
            continue

        registry.update_status(
            current_url,
            URLStatus.CRAWLING,
        )

        try:
            html = await fetch_page(current_url)

            title, content = parse_page(html)

            links = extract_links(
                html,
                current_url,
            )

        except Exception as error:

            registry.update_status(
                current_url,
                URLStatus.FAILED,
                str(error),
            )

            continue

        page = CrawledPage(
            url=current_url,
            title=title,
            content=content,
            links=links,
            status="success",
        )

        pages.append(page)

        registry.update_status(
            current_url,
            URLStatus.CRAWLED,
        )

        for link in links:

            if registry.get(link):
                continue

            registry.add(
                link,
                status=URLStatus.QUEUED,
                depth=record.depth + 1,
                discovered_from=current_url,
            )

            queue.append(link)

    return pages, registry