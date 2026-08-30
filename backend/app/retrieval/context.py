def build_context(results) -> str:
    sources = {}

    for chunk, url, title, distance in results:
        source = sources.setdefault(url, {"title": title, "chunks": []})
        if chunk.content not in source["chunks"]:
            source["chunks"].append(chunk.content)

    parts = []
    for index, (url, source) in enumerate(sources.items(), start=1):
        content = "\n\n".join(source["chunks"])
        parts.append(
            f"SOURCE {index}\n"
            f"Title: {source['title'] or 'Untitled page'}\n"
            f"URL: {url}\n"
            f"Content:\n{content}"
        )

    return "\n\n---\n\n".join(parts)
