import pytest
from unittest.mock import patch, MagicMock
from app.crawler.ssrf import validate_url_safety, SSRFError, is_safe_ip
from app.crawler.fetcher import fetch_page


def test_is_safe_ip():
    assert is_safe_ip("8.8.8.8") is True
    assert is_safe_ip("1.1.1.1") is True
    
    assert is_safe_ip("127.0.0.1") is False
    assert is_safe_ip("::1") is False
    assert is_safe_ip("10.0.0.1") is False
    assert is_safe_ip("192.168.1.1") is False
    assert is_safe_ip("172.16.0.1") is False
    assert is_safe_ip("169.254.169.254") is False
    assert is_safe_ip("224.0.0.1") is False # multicast


@patch("app.crawler.ssrf.resolve_hostname")
def test_validate_url_safety_public(mock_resolve):
    mock_resolve.return_value = ["8.8.8.8"]
    assert validate_url_safety("http://example.com") is True
    assert validate_url_safety("https://example.com/path?q=1") is True


@patch("app.crawler.ssrf.resolve_hostname")
def test_validate_url_safety_invalid_scheme(mock_resolve):
    with pytest.raises(SSRFError, match="Invalid scheme"):
        validate_url_safety("ftp://example.com")
        
    with pytest.raises(SSRFError, match="Invalid scheme"):
        validate_url_safety("file:///etc/passwd")


@patch("app.crawler.ssrf.resolve_hostname")
def test_validate_url_safety_private(mock_resolve):
    # localhost
    mock_resolve.return_value = ["127.0.0.1"]
    with pytest.raises(SSRFError, match="unsafe IP"):
        validate_url_safety("http://localhost")
        
    # metadata
    mock_resolve.return_value = ["169.254.169.254"]
    with pytest.raises(SSRFError, match="unsafe IP"):
        validate_url_safety("http://169.254.169.254")
        
    # private dns resolution
    mock_resolve.return_value = ["10.0.0.5"]
    with pytest.raises(SSRFError, match="unsafe IP"):
        validate_url_safety("http://internal-admin.local")


@pytest.mark.anyio
async def test_fetcher_blocks_ssrf_initial():
    with patch("app.crawler.fetcher.validate_url_safety", side_effect=SSRFError("Blocked")):
        with pytest.raises(ValueError, match="SSRF blocked: Blocked"):
            await fetch_page("http://127.0.0.1")


@pytest.mark.anyio
async def test_fetcher_blocks_ssrf_redirect():
    from app.crawler.fetcher import _check_ssrf
    import httpx
    
    req1 = httpx.Request("GET", "http://example.com")
    req2 = httpx.Request("GET", "http://127.0.0.1")
    
    with patch("app.crawler.ssrf.resolve_hostname") as mock_resolve:
        mock_resolve.return_value = ["8.8.8.8"]
        await _check_ssrf(req1)
        
        mock_resolve.return_value = ["127.0.0.1"]
        with pytest.raises(ValueError, match="SSRF blocked"):
            await _check_ssrf(req2)


@pytest.mark.anyio
async def test_fetcher_allows_safe_urls():
    # If validate_url_safety passes, it should attempt the fetch.
    # We will mock the actual network call to avoid real HTTP requests.
    with patch("app.crawler.fetcher.validate_url_safety", return_value=True):
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_response.text = "<html></html>"
            mock_get.return_value = mock_response
            
            content, status = await fetch_page("http://example.com")
            assert status == 200
            assert content == "<html></html>"
