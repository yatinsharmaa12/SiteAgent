from bs4 import BeautifulSoup


def parse_page(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""

    content_lines = []

    for element in soup.find_all(
        ["h1", "h2", "h3", "p", "li"]
    ):
        text = element.get_text(" ", strip=True)

        if not text:
            continue

        if element.name == "h1":
            text = f"# {text}"
        elif element.name == "h2":
            text = f"## {text}"
        elif element.name == "h3":
            text = f"### {text}"

        content_lines.append(text)

    content = "\n".join(content_lines)

    return title, content