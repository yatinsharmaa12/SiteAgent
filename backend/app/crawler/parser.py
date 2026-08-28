from bs4 import BeautifulSoup


def parse_page(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""

    text = soup.get_text(separator="\n")

    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    cleaned_lines = []

    for line in lines:
        if not cleaned_lines or line != cleaned_lines[-1]:
            cleaned_lines.append(line)

    content = "\n".join(cleaned_lines)

    return title, content