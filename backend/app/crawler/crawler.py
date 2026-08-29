import hashlib
from collections import deque
from urllib.parse import urlparse

from app.crawler.url_filter import is_crawlable_url
from app.crawler.fetcher import fetch_page
from app.crawler.parser import parse_page
from app.crawler.link_extractor import extract_links, normalize_url
from app.crawler.url_registry import URLRegistry
from app.crawler.robots import RobotsChecker

from app.ingestion.embedding import EmbeddingModel
from app.ingestion.ingest import ingest_page

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

    # URLs processed during THIS crawl only.
    visited_this_crawl = set()

    registry = URLRegistry(
        db=db,
        company_id=company_id,
    )

    page_repository = PageRepository(db)

    # Load embedding model once for the entire crawl.
    embedder = EmbeddingModel()

    robots = RobotsChecker(start_url)
    await robots.load()

    pages = []

    start_domain = urlparse(start_url).hostname

    # Make sure the start URL is available for this crawl.
    registry.add(
        start_url,
        status=URLStatus.QUEUED,
        depth=0,
    )

    registry.update_status(
        start_url,
        URLStatus.QUEUED,
    )

    while queue and len(pages) < max_pages:

        current_url, current_depth = queue.popleft()

        # Prevent loops within the current crawl.
        if current_url in visited_this_crawl:
            continue

        visited_this_crawl.add(current_url)

        record = registry.get(current_url)

        if not record:
            continue

        # INDEXED means this URL should not be crawled.
        if record.status == URLStatus.INDEXED:
            continue

        if urlparse(current_url).hostname != start_domain:
            continue

        if current_depth > max_depth:
            continue

        # Respect robots.txt.
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
            # -------------------------------------------------
            # FETCH
            # -------------------------------------------------
            html, http_status = await fetch_page(
                current_url
            )

            # -------------------------------------------------
            # PARSE
            # -------------------------------------------------
            title, content = parse_page(html)

            # -------------------------------------------------
            # EXTRACT LINKS
            # -------------------------------------------------
            links = extract_links(
                html,
                current_url,
                depth=current_depth + 1,
            )

            # -------------------------------------------------
            # CONTENT HASH
            # -------------------------------------------------
            content_hash = hashlib.sha256(
                content.encode("utf-8")
            ).hexdigest()

            # -------------------------------------------------
            # FIND URL RECORD
            # -------------------------------------------------
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

            # -------------------------------------------------
            # CHECK WHETHER PAGE ALREADY EXISTS
            # -------------------------------------------------
            existing_page = page_repository.get_by_url(
                company_id=company_id,
                url_id=db_url.id,
            )

            # -------------------------------------------------
            # NEW PAGE
            # -------------------------------------------------
            if existing_page is None:

                page = page_repository.create(
                    company_id=company_id,
                    url_id=db_url.id,
                    url=current_url,
                    title=title,
                    content=content,
                    http_status=http_status,
                    content_hash=content_hash,
                )

                ingest_page(
                    page.id,
                    db=db,
                    embedder=embedder,
                )

                print(
                    f"Created and ingested Page {page.id}"
                )

            # -------------------------------------------------
            # EXISTING PAGE
            # -------------------------------------------------
            else:

                page = existing_page

                # Content changed.
                if page.content_hash != content_hash:

                    page_repository.update(
                        page=page,
                        title=title,
                        content=content,
                        http_status=http_status,
                        content_hash=content_hash,
                    )

                    ingest_page(
                        page.id,
                        db=db,
                        embedder=embedder,
                        replace_existing=True,
                    )

                    print(
                        f"Updated and re-ingested Page {page.id}"
                    )

                # Content unchanged.
                else:

                    print(
                        f"Page {page.id} unchanged, "
                        f"skipping ingestion"
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

        # -----------------------------------------------------
        # SUCCESSFUL CRAWL RESULT
        # -----------------------------------------------------
        page_result = CrawledPage(
            url=current_url,
            title=title,
            content=content,
            links=links,
            status="success",
        )

        pages.append(page_result)

        registry.update_status(
            current_url,
            URLStatus.CRAWLED,
            http_status=http_status,
        )

        # -----------------------------------------------------
        # DISCOVER NEW LINKS
        # -----------------------------------------------------
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

            # Only skip if we already processed this URL
            # during THIS crawl.
            if link in visited_this_crawl:
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