from app.rag.generator import GeminiGenerator
from app.rag.prompt import build_prompt
from app.retrieval.context import build_context
from app.retrieval.search import search_chunks


def answer_question(
    question: str,
    company_id: int,
) -> dict:
    results = search_chunks(
        question,
        company_id=company_id,
    )

    if not results:
        return {
            "answer": "The website does not provide enough information to answer that.",
            "sources": [],
        }

    context = build_context(results)
    prompt = build_prompt(question, context)

    generator = GeminiGenerator()
    answer = generator.generate(prompt)

    sources = []
    seen_urls = set()

    for chunk, url, title, distance in results:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        sources.append({"title": title, "url": url})

    return {
        "answer": answer,
        "sources": sources,
    }
