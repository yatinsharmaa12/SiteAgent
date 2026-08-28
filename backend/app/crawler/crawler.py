import hashlib
from collections import deque
from urllib.parse import urlparse

from app.crawler.url_filter import is_crawlable_url
from app.crawler.fetcher import fetch_page
from app.crawler.parser import parse_page
from app.crawler.link_extractor import extract_links, normalize_url
from app.crawler.url_registry import URLRegistry
from app.crawler.robots import RobotsChecker

from app.models.page import CrawledPage
from app.models.url import URLStatus
from app.models.url_db import URL

from app.repositories.page_repository import PageRepository


async def crawl_site(
    start_url: str,
    db,
    company_id: int,
    max_pages: int = 5,
    max_depth: int = 1,
) -> tuple[list[CrawledPage], URLRegistry]:

    normalized_start_url = normalize_url(
        start_url,
        start_url,
    )

    if not normalized_start_url:
        raise ValueError(
            f"Invalid start URL: {start_url}"
        )

    start_url = normalized_start_url

    queue = deque([(start_url, 0)])

    registry = URLRegistry(
        db=db,
        company_id=company_id,
    )

    page_repository = PageRepository(db)

    robots = RobotsChecker(start_url)
    await robots.load()

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

        if current_depth > max_depth:
            continue

        # Respect robots.txt
        if not robots.can_fetch(current_url):
            registry.update_status(
                current_url,
                URLStatus.SKIPPED,
            )
            continue

        registry.update_status(
            current_url,
            URLStatus.CRAWLING,
        )

        try:
            html, http_status = await fetch_page(
                current_url
            )

            title, content = parse_page(html)

            links = extract_links(
                html,
                current_url,
                depth=current_depth + 1,
            )

            content_hash = hashlib.sha256(
                content.encode("utf-8")
            ).hexdigest()

            db_url = (
                db.query(URL)
                .filter(
                    URL.company_id == company_id,
                    URL.normalized_url == current_url,
                )
                .first()
            )

            if not db_url:
                raise ValueError(
                    f"URL record not found: {current_url}"
                )

            page_repository.create(
                company_id=company_id,
                url_id=db_url.id,
                url=current_url,
                title=title,
                content=content,
                http_status=http_status,
                content_hash=content_hash,
            )

        except Exception as error:

            print(
                f"CRAWL ERROR: {current_url} -> {error}"
            )

            registry.update_status(
                current_url,
                URLStatus.FAILED,
                str(error),
                http_status=None,
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
            http_status=http_status,
        )

        for link in links:

            if not is_crawlable_url(link):
                continue

            if not robots.can_fetch(link):
                registry.add(
                    link,
                    status=URLStatus.SKIPPED,
                    depth=current_depth + 1,
                    discovered_from=current_url,
                )
                continue

            if registry.get(link):
                continue

            next_depth = current_depth + 1

            registry.add(
                link,
                status=URLStatus.QUEUED,
                depth=next_depth,
                discovered_from=current_url,
            )

            if next_depth <= max_depth:
                queue.append(
                    (link, next_depth)
                )

    return pages, registry