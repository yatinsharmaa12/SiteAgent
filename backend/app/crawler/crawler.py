import hashlib
from collections import deque
from typing import Optional
from urllib.parse import urlparse

from app.crawler.url_filter import is_crawlable_url
from app.crawler.fetcher import fetch_page
from app.crawler.parser import parse_page
from app.crawler.link_extractor import extract_links, normalize_url
from app.crawler.url_registry import URLRegistry
from app.crawler.robots import RobotsChecker

from app.ingestion.embedding import EmbeddingModel
from app.ingestion.ingest import ingest_page

from app.models.crawl_job import CrawlJob
from app.models.page import CrawledPage
from app.models.url import URLStatus
from app.models.url_db import URL

from app.repositories.page_repository import PageRepository


def update_crawl_progress(
    db,
    crawl_job: CrawlJob,
):
    urls = (
        db.query(URL)
        .filter(
            URL.company_id == crawl_job.company_id,
        )
        .all()
    )

    crawl_job.pages_discovered = len(urls)

    crawl_job.pages_crawled = sum(
        1
        for url in urls
        if url.status in {
            "crawled",
            "indexed",
        }
    )

    crawl_job.pages_indexed = sum(
        1
        for url in urls
        if url.status == "indexed"
    )

    crawl_job.pages_failed = sum(
        1
        for url in urls
        if url.status == "failed"
    )

    db.commit()


async def crawl_site(
    start_url: str,
    db,
    company_id: int,
    max_pages: int = 5,
    max_depth: int = 1,
    crawl_job: Optional[CrawlJob] = None,
) -> tuple[list[CrawledPage], URLRegistry]:

    # -------------------------------------------------
    # NORMALIZE START URL
    # -------------------------------------------------

    normalized_start_url = normalize_url(
        start_url,
        start_url,
    )

    if not normalized_start_url:
        raise ValueError(
            f"Invalid start URL: {start_url}"
        )

    start_url = normalized_start_url

    # -------------------------------------------------
    # CRAWL QUEUE
    # -------------------------------------------------

    queue = deque([
        (start_url, 0)
    ])

    # URLs processed during THIS crawl only.
    visited_this_crawl = set()

    # -------------------------------------------------
    # SERVICES
    # -------------------------------------------------

    registry = URLRegistry(
        db=db,
        company_id=company_id,
    )

    page_repository = PageRepository(db)

    # Load embedding model once for entire crawl.
    embedder = EmbeddingModel()

    # -------------------------------------------------
    # ROBOTS.TXT
    # -------------------------------------------------

    robots = RobotsChecker(start_url)

    await robots.load()

    # -------------------------------------------------
    # RESULTS
    # -------------------------------------------------

    pages = []

    start_domain = urlparse(
        start_url
    ).hostname

    # -------------------------------------------------
    # REGISTER START URL
    # -------------------------------------------------

    registry.add(
        start_url,
        status=URLStatus.QUEUED,
        depth=0,
    )

    registry.update_status(
        start_url,
        URLStatus.QUEUED,
    )

    if crawl_job:
        update_crawl_progress(
            db,
            crawl_job,
        )

    # -------------------------------------------------
    # MAIN CRAWL LOOP
    # -------------------------------------------------

    while queue and len(pages) < max_pages:

        current_url, current_depth = queue.popleft()

        # -------------------------------------------------
        # PREVENT DUPLICATES
        # -------------------------------------------------

        if current_url in visited_this_crawl:
            continue

        visited_this_crawl.add(
            current_url
        )

        # -------------------------------------------------
        # GET URL REGISTRY RECORD
        # -------------------------------------------------

        record = registry.get(
            current_url
        )

        if not record:
            continue

        # Already indexed.
        if record.status == URLStatus.INDEXED:
            continue

        # -------------------------------------------------
        # DOMAIN CHECK
        # -------------------------------------------------

        if urlparse(
            current_url
        ).hostname != start_domain:
            continue

        # -------------------------------------------------
        # DEPTH CHECK
        # -------------------------------------------------

        if current_depth > max_depth:
            continue

        # -------------------------------------------------
        # ROBOTS CHECK
        # -------------------------------------------------

        if not robots.can_fetch(
            current_url
        ):

            registry.update_status(
                current_url,
                URLStatus.SKIPPED,
            )

            if crawl_job:
                update_crawl_progress(
                    db,
                    crawl_job,
                )

            continue

        # -------------------------------------------------
        # MARK AS CRAWLING
        # -------------------------------------------------

        registry.update_status(
            current_url,
            URLStatus.CRAWLING,
        )

        # -------------------------------------------------
        # FETCH + PARSE + INGEST
        # -------------------------------------------------

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

            title, content = parse_page(
                html
            )

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
            # FIND URL DATABASE RECORD
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
            # CHECK EXISTING PAGE
            # -------------------------------------------------

            existing_page = (
                page_repository.get_by_url(
                    company_id=company_id,
                    url_id=db_url.id,
                )
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

                # -------------------------------------------------
                # CONTENT CHANGED
                # -------------------------------------------------

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

                # -------------------------------------------------
                # CONTENT UNCHANGED
                # -------------------------------------------------

                else:

                    print(
                        f"Page {page.id} unchanged, "
                        f"skipping ingestion"
                    )

        # -------------------------------------------------
        # CRAWL ERROR
        # -------------------------------------------------

        except Exception as error:

            print(
                f"CRAWL ERROR: {current_url} -> {error}"
            )

            error_http_status = None

            response = getattr(
                error,
                "response",
                None,
            )

            if response is not None:
                error_http_status = getattr(
                    response,
                    "status_code",
                    None,
                )

            registry.update_status(
                current_url,
                URLStatus.FAILED,
                str(error),
                http_status=error_http_status,
            )

            # Update job progress even when page fails.
            if crawl_job:
                update_crawl_progress(
                    db,
                    crawl_job,
                )

            continue

        # -------------------------------------------------
        # SUCCESSFUL CRAWL RESULT
        # -------------------------------------------------

        page_result = CrawledPage(
            url=current_url,
            title=title,
            content=content,
            links=links,
            status="success",
        )

        pages.append(
            page_result
        )

        # -------------------------------------------------
        # UPDATE URL STATUS
        # -------------------------------------------------

        registry.update_status(
            current_url,
            URLStatus.CRAWLED,
            http_status=http_status,
        )

        registry.update_status(
            current_url,
            URLStatus.INDEXED,
            http_status=http_status,
        )

        # -------------------------------------------------
        # UPDATE PROGRESS
        # -------------------------------------------------

        if crawl_job:
            update_crawl_progress(
                db,
                crawl_job,
            )

        # -------------------------------------------------
        # DISCOVER NEW LINKS
        # -------------------------------------------------

        for link in links:

            # -------------------------------------------------
            # FILE / URL FILTER
            # -------------------------------------------------

            if not is_crawlable_url(
                link
            ):
                continue

            # -------------------------------------------------
            # ROBOTS CHECK
            # -------------------------------------------------

            if not robots.can_fetch(
                link
            ):

                registry.add(
                    link,
                    status=URLStatus.SKIPPED,
                    depth=current_depth + 1,
                    discovered_from=current_url,
                )

                continue

            # -------------------------------------------------
            # ALREADY VISITED
            # -------------------------------------------------

            if link in visited_this_crawl:
                continue

            next_depth = (
                current_depth + 1
            )

            # -------------------------------------------------
            # REGISTER URL
            # -------------------------------------------------

            registry.add(
                link,
                status=URLStatus.QUEUED,
                depth=next_depth,
                discovered_from=current_url,
            )

            # -------------------------------------------------
            # ADD TO QUEUE
            # -------------------------------------------------

            if next_depth <= max_depth:

                queue.append(
                    (
                        link,
                        next_depth,
                    )
                )

        # -------------------------------------------------
        # UPDATE PROGRESS AFTER DISCOVERY
        # -------------------------------------------------

        if crawl_job:
            update_crawl_progress(
                db,
                crawl_job,
            )

    # -------------------------------------------------
    # FINAL PROGRESS UPDATE
    # -------------------------------------------------

    if crawl_job:
        update_crawl_progress(
            db,
            crawl_job,
        )

    return pages, registry