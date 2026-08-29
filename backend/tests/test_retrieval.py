from unittest.mock import MagicMock, patch

from app.retrieval.search import search_chunks


def test_retrieval_filters_by_distance():
    mock_query = MagicMock()

    # Match the full SQLAlchemy query chain.
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query

    mock_query.all.return_value = [
        (
            "chunk1",
            "https://example.com",
            "Example",
            0.30,
        )
    ]

    mock_db = MagicMock()
    mock_db.query.return_value = mock_query

    with patch(
        "app.retrieval.search.SessionLocal",
        return_value=mock_db,
    ), patch(
        "app.retrieval.search.EmbeddingModel"
    ) as mock_embedding:

        mock_embedding.return_value.embed.return_value = [
            0.1
        ] * 384

        results = search_chunks(
            "What is the website about?",
            company_id=1,
            max_distance=0.80,
        )

    assert len(results) == 1
    assert results[0][3] == 0.30