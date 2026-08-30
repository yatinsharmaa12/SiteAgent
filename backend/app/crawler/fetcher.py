import httpx


TIMEOUT = 10.0

ALLOWED_CONTENT_TYPES = {
    "text/html",
    "application/xhtml+xml",
}


async def fetch_page(url: str) -> tuple[str, int]:
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=TIMEOUT,
        headers={
            "User-Agent": "SiteAgent/1.0",
        },
    ) as client:

        response = await client.get(url)

        content_type = response.headers.get(
            "content-type",
            ""
        ).split(";")[0].strip().lower()

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

        return response.text, response.status_code