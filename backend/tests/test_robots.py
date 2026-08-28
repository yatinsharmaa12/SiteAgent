import pytest

from app.crawler.robots import RobotsChecker


@pytest.mark.anyio
async def test_robots_allows_public_page():
    checker = RobotsChecker("https://example.com")

    await checker.load()

    assert checker.can_fetch(
        "https://example.com/"
    )


@pytest.mark.anyio
async def test_robots_checker_requires_load():
    checker = RobotsChecker("https://example.com")

    with pytest.raises(RuntimeError):
        checker.can_fetch(
            "https://example.com/"
        )