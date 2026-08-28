from bs4 import BeautifulSoup


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Remove elements that don't contain useful knowledge
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    # Extract visible text
    text = soup.get_text(separator="\n")

    # Clean empty lines and whitespace
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
     
    cleaned_lines = []
    for line in lines:
        if not cleaned_lines or line != cleaned_lines[-1]:
            cleaned_lines.append(line)


    print("LINES:")
    for i, line in enumerate(lines):
        print(i, repr(line))

    

    return "\n".join(cleaned_lines)