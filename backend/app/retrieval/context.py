def _escape_source_text(text: str) -> str:
    # Prevent tag breakout: a crawled page containing </website_source>
    # must not be able to close our delimiter early.
    if not text:
        return text
    return (
        text.replace("</website_source>", "[blocked-tag]")
        .replace("<website_source", "[blocked-tag]")
        .replace("</website_sources>", "[blocked-tag]")
        .replace("<website_sources", "[blocked-tag]")
    )


def build_context(results) -> str:
    sources = {}

    for chunk, url, title, distance in results:
        source = sources.setdefault(url, {"title": title, "chunks": []})
        if chunk.content not in source["chunks"]:
            source["chunks"].append(chunk.content)

    parts = []
    for index, (url, source) in enumerate(sources.items(), start=1):
        content = "\n\n".join(source["chunks"])
        title = _escape_source_text(source["title"] or "Untitled page")
        safe_url = _escape_source_text(url)
        safe_content = _escape_source_text(content)
        parts.append(
            f'<website_source id="{index}">\n'
            f"SOURCE {index}\n"
            f"Title: {title}\n"
            f"URL: {safe_url}\n"
            f"Content:\n{safe_content}\n"
            f"</website_source>"
        )

    return "\n\n---\n\n".join(parts)
