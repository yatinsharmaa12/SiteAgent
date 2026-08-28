from urllib.parse import urljoin, urlparse, urlunparse, urldefrag
from typing import Optional
from bs4 import BeautifulSoup


TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
}

VOLATILE_PARAMS = {
    "token",
    "session",
    "sessionid",
    "sid",
}

def normalize_url(url: str, base_url: str) -> Optional[str]:
    # Convert relative URL to absolute URL
    url = urljoin(base_url, url)

    # Remove fragment
    url, _ = urldefrag(url)

    parsed = urlparse(url)

    # Only HTTP/HTTPS
    if parsed.scheme not in ("http", "https"):
        return None

    # Remove username/password
    if parsed.username or parsed.password:
        return None

    # Lowercase domain
    hostname = parsed.hostname
    if not hostname:
        return None

    hostname = hostname.lower()

    # Remove default ports
    if parsed.port:
        if (parsed.scheme == "http" and parsed.port != 80) or (
            parsed.scheme == "https" and parsed.port != 443
        ):
            hostname = f"{hostname}:{parsed.port}"

    # Normalize path
    path = parsed.path or "/"

    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # Keep legitimate query parameters,
    # but remove common tracking parameters
    query_parts = []

    if parsed.query:
        for parameter in parsed.query.split("&"):
            if "=" in parameter:
                key, value = parameter.split("=", 1)
            else:
                key, value = parameter, ""

            if (
                key.lower() not in TRACKING_PARAMS
                and key.lower() not in VOLATILE_PARAMS
            ):
                query_parts.append(
                f"{key}={value}" if value else key
                )

    query = "&".join(query_parts)

    return urlunparse(
        (
            parsed.scheme,
            hostname,
            path,
            "",
            query,
            "",
        )
    )


def extract_links(
    html: str,
    base_url: str,
    depth: int = 0,
) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")

    base_domain = urlparse(base_url).hostname

    discovered_urls = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()

        normalized_url = normalize_url(href, base_url)

        if not normalized_url:
            continue

        parsed = urlparse(normalized_url)

        # Same-domain only
        if parsed.hostname != base_domain:
            continue

        discovered_urls.add(normalized_url)

    return sorted(discovered_urls)