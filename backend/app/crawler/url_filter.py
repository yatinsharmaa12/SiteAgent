from urllib.parse import urlparse


IGNORED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".zip",
    ".mp4",
    ".mp3",
    ".avi",
    ".mov",
}


def is_crawlable_url(url: str) -> bool:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        return False

    path = parsed.path.lower()

    for extension in IGNORED_EXTENSIONS:
        if path.endswith(extension):
            return False

    return True