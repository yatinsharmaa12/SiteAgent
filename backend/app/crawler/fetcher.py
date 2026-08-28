import httpx


async def fetch_page(url: str) -> tuple[str, int]:
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=10.0,
    ) as client:
        response = await client.get(url)

        return response.text, response.status_code