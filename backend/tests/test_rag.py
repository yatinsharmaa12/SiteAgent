from app.rag.prompt import build_prompt
from app.retrieval.context import build_context
from unittest.mock import patch

from app.rag.pipeline import answer_question


class FakeChunk:
    def __init__(self, content):
        self.content = content


def test_build_context():
    results = [
        (
            FakeChunk("Customer name and telephone."),
            "https://example.com/order",
            "Order Form",
            0.3,
        )
    ]

    context = build_context(results)

    assert "[Source: Order Form]" in context
    assert "[URL: https://example.com/order]" in context
    assert "Customer name and telephone." in context


def test_build_prompt_contains_question_and_context():
    context = "The website offers three pricing plans."
    question = "How many pricing plans are there?"

    prompt = build_prompt(
        question,
        context,
    )

    assert context in prompt
    assert question in prompt
    assert "Do not invent facts." in prompt

def test_answer_question_when_no_context():
    with patch(
        "app.rag.pipeline.search_chunks",
        return_value=[],
    ):
        result = answer_question(
            question="What is the refund policy?",
            company_id=1,
        )

    assert result["answer"] == (
        "I don't have enough information to answer that."
    )
    assert result["sources"] == []

def test_answer_question_returns_answer_and_sources():
    fake_chunk = FakeChunk(
        "Bacon is available as an order topping."
    )

    fake_results = [
        (
            fake_chunk,
            "https://httpbin.org/forms/post",
            "Order Form",
            0.39,
        )
    ]

    with patch(
        "app.rag.pipeline.search_chunks",
        return_value=fake_results,
    ), patch(
        "app.rag.pipeline.GeminiGenerator"
    ) as mock_generator:

        mock_generator.return_value.generate.return_value = (
            "Bacon is available as a topping."
        )

        result = answer_question(
            question="Can I order bacon?",
            company_id=1,
        )

    assert result["answer"] == (
        "Bacon is available as a topping."
    )

    assert result["sources"] == [
        {
            "title": "Order Form",
            "url": "https://httpbin.org/forms/post",
        }
    ]