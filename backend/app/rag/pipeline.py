from app.rag.generator import GeminiGenerator
from app.rag.prompt import build_prompt
from app.retrieval.context import build_context
from app.retrieval.search import search_chunks


def answer_question(question: str) -> dict:
    results = search_chunks(question)

    if not results:
        return {
            "answer": "I don't have enough information to answer that.",
            "sources": [],
        }

    context = build_context(results)
    prompt = build_prompt(question, context)

    generator = GeminiGenerator()
    answer = generator.generate(prompt)

    sources = []

    for chunk, url, title, distance in results:
        source = {
            "title": title,
            "url": url,
        }

        if source not in sources:
            sources.append(source)

    return {
        "answer": answer,
        "sources": sources,
    }