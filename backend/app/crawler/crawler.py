from collections import deque
from urllib.parse import urlparse

from app.crawler.fetcher import fetch_page
from app.crawler.parser import parse_page
from app.crawler.link_extractor import extract_links
from app.models.page import CrawledPage


async def crawl_site(
    start_url: str,
    max_pages: int = 5,
) -> list[CrawledPage]:

    queue = deque([start_url])
    visited = set()
    pages = []

    start_domain = urlparse(start_url).hostname

    while queue and len(pages) < max_pages:
        current_url = queue.popleft()

        if current_url in visited:
            continue

        if urlparse(current_url).hostname != start_domain:
            continue

        visited.add(current_url)

        try:
            html = await fetch_page(current_url)
            title, content = parse_page(html)
            links = extract_links(html, current_url)

        except Exception as error:
            print(f"Failed to crawl {current_url}: {error}")
            continue

        page = CrawledPage(
            url=current_url,
            title=title,
            content=content,
            links=links,
            status="success",
        )

        pages.append(page)

        for link in links:
            if link not in visited and link not in queue:
                queue.append(link)

    return pages