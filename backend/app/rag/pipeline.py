from app.rag.generator import GeminiGenerator
from app.rag.prompt import build_prompt
from app.retrieval.context import build_context
from app.retrieval.search import search_chunks


def answer_question(question: str) -> str:
    results = search_chunks(question)

    if not results:
        return "I don't have enough information to answer that."

    context = build_context(results)
    prompt = build_prompt(question, context)

    generator = GeminiGenerator()

    return generator.generate(prompt)