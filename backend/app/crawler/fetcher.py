import httpx


async def fetch_page(url: str) -> str:
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=10.0,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

        return response.text