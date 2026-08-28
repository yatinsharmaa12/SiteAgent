from app.crawler.link_extractor import normalize_url


BASE_URL = "https://Example.com/products/"


def test_relative_url():
    assert normalize_url("/pricing", BASE_URL) == "https://example.com/pricing"


def test_trailing_slash():
    assert normalize_url("/pricing/", BASE_URL) == "https://example.com/pricing"


def test_fragment_removed():
    assert normalize_url("/pricing#plans", BASE_URL) == "https://example.com/pricing"


def test_tracking_parameter_removed():
    assert (
        normalize_url(
            "/pricing?utm_source=google",
            BASE_URL,
        )
        == "https://example.com/pricing"
    )


def test_legitimate_query_parameter_kept():
    assert (
        normalize_url(
            "/products?id=123&utm_source=google",
            BASE_URL,
        )
        == "https://example.com/products?id=123"
    )


def test_mailto_rejected():
    assert normalize_url("mailto:test@example.com", BASE_URL) is None


def test_javascript_rejected():
    assert normalize_url("javascript:void(0)", BASE_URL) is None