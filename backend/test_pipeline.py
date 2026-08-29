import asyncio

from app.crawler.fetcher import fetch_page
from app.crawler.parser import parse_page
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import chunk_text
import tiktoken


async def test():
    html, status = await fetch_page("https://redis.com/")

    title, content = parse_page(html)

    cleaned = clean_text(content)

    chunks = chunk_text(cleaned, chunk_size=500)

    encoding = tiktoken.get_encoding("cl100k_base")

    print("Characters:", len(chunks[0]))
    print("Tokens:", len(encoding.encode(chunks[0])))

    print("Title:", title)
    print("Number of chunks:", len(chunks))

    for i, chunk in enumerate(chunks):
        print(
            f"Chunk {i}: "
            f"{len(chunk)} chars, "
            f"{len(encoding.encode(chunk))} tokens"
        )

    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {i} ---")
        print(chunk)


asyncio.run(test())
