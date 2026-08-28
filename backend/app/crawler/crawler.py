from collections import deque
from urllib.parse import urlparse

from app.crawler.fetcher import fetch_page
from app.crawler.link_extractor import extract_links


async def crawl_site(start_url: str, max_pages: int = 5) -> list[dict]:
    queue = deque([start_url])
    visited = set()
    pages = []

    start_domain = urlparse(start_url).hostname

    while queue and len(pages) < max_pages:
        current_url = queue.popleft()

        # Skip URLs we have already visited
        if current_url in visited:
            continue

        # Safety check: only crawl the starting domain
        if urlparse(current_url).hostname != start_domain:
            continue

        visited.add(current_url)

        try:
            html = await fetch_page(current_url)
        except Exception as error:
            print(f"Failed to crawl {current_url}: {error}")
            continue

        links = extract_links(html, current_url)

        pages.append({
            "url": current_url,
            "links_found": len(links),
        })

        # Add newly discovered URLs to the queue
        for link in links:
            if link not in visited and link not in queue:
                queue.append(link)

    return pages