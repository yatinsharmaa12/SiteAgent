import httpx

from app.crawler.exceptions import RetryableCrawlError, CrawlTimeoutError, ResourceLimitError
from app.crawler.ssrf import dns_pinning, validate_url_safety, SSRFError
from app.core.config import (
    MAX_RESPONSE_SIZE_BYTES,
    REQUEST_CONNECT_TIMEOUT,
    REQUEST_READ_TIMEOUT,
    REQUEST_WRITE_TIMEOUT,
    REQUEST_POOL_TIMEOUT,
)


TIMEOUT = httpx.Timeout(
    connect=REQUEST_CONNECT_TIMEOUT,
    read=REQUEST_READ_TIMEOUT,
    write=REQUEST_WRITE_TIMEOUT,
    pool=REQUEST_POOL_TIMEOUT,
)

ALLOWED_CONTENT_TYPES = {
    "text/html",
    "application/xhtml+xml",
}


async def _check_ssrf(request: httpx.Request):
    try:
        validate_url_safety(str(request.url))
    except SSRFError as e:
        raise ValueError(f"SSRF blocked: {e}")


async def fetch_page(url: str) -> tuple[str, int]:
    try:
        # Pin DNS for the whole fetch so validation and connect (including
        # redirects, each re-validated by _check_ssrf) see the same IPs.
        with dns_pinning():
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=TIMEOUT,
                headers={
                    "User-Agent": "SiteAgent/1.0",
                },
                event_hooks={
                    "request": [_check_ssrf]
                }
            ) as client:

                async with client.stream("GET", url) as response:
                    chunks: list[bytes] = []
                    response_size = 0

                    async for chunk in response.aiter_bytes():
                        response_size += len(chunk)
                        if response_size > MAX_RESPONSE_SIZE_BYTES:
                            raise ResourceLimitError(
                                f"Response size {response_size} exceeds maximum {MAX_RESPONSE_SIZE_BYTES} bytes"
                            )
                        chunks.append(chunk)

                    body = b"".join(chunks)

                content_type = response.headers.get(
                    "content-type",
                    "",
                ).split(";")[0].strip().lower()

                if response.status_code >= 500:
                    raise RetryableCrawlError(
                        f"Server error HTTP {response.status_code}"
                    )

                if response.status_code >= 400:
                    raise httpx.HTTPStatusError(
                        f"HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                if content_type not in ALLOWED_CONTENT_TYPES:
                    raise ValueError(
                        f"Unsupported content type: {content_type}"
                    )

                encoding = response.encoding or "utf-8"
                return body.decode(encoding, errors="replace"), response.status_code

    except RetryableCrawlError:
        raise

    except (
        httpx.TimeoutException,
        httpx.NetworkError,
        httpx.ConnectError,
        httpx.ReadError,
    ) as error:

        raise CrawlTimeoutError(
            f"Temporary network error: {error}"
        ) from error
