import asyncio
from bs4 import BeautifulSoup

from app.crawler.fetcher import fetch_page


def extract_sections(html: str):
    soup = BeautifulSoup(html, "html.parser")

    sections = []

    for heading in soup.find_all(["h1", "h2", "h3"]):
        heading_text = heading.get_text(" ", strip=True)

        if not heading_text:
            continue

        content = []

        for element in heading.find_all_next():
            if element.name in ["h1", "h2", "h3"]:
                break

            if element.name in ["p", "li"]:
                text = element.get_text(" ", strip=True)

                if text:
                    content.append(text)

        sections.append({
            "heading": heading_text,
            "content": content,
        })

    return sections


async def test():
    html, status = await fetch_page("https://redis.com/")

    sections = extract_sections(html)

    for section in sections[:5]:
        print("\nHEADING:", section["heading"])

        for text in section["content"][:3]:
            print("-", text)


asyncio.run(test())