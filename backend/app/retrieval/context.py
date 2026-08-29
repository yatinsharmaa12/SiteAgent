def build_context(results) -> str:
    parts = []

    for chunk, url, title, distance in results:
        parts.append(
            f"[Source: {title}]\n"
            f"[URL: {url}]\n"
            f"{chunk.content}"
        )

    return "\n\n---\n\n".join(parts)