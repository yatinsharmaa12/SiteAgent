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
    max_depth: int = 1,
) -> tuple[list[CrawledPage], URLRegistry]:

    queue = deque([(start_url, 0)])
    registry = URLRegistry()
    pages = []

    start_domain = urlparse(start_url).hostname

    registry.add(
        start_url,
        status=URLStatus.QUEUED,
        depth=0,
    )

    while queue and len(pages) < max_pages:

        current_url, current_depth = queue.popleft()

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

        # Don't crawl beyond the allowed depth
        if current_depth > max_depth:
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
                depth=current_depth + 1,
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

        # Register discovered links
        for link in links:

            if registry.get(link):
                continue

            next_depth = current_depth + 1

            registry.add(
                link,
                status=URLStatus.QUEUED,
                depth=next_depth,
                discovered_from=current_url,
            )

            # Only crawl URLs within the allowed depth
            if next_depth <= max_depth:

                print(
                    f"DISCOVERED: {link} | "
                    f"depth={next_depth} | "
                    f"max_depth={max_depth}"
                )

                queue.append(
                    (link, next_depth)
                )

    return pages, registry