class RetryableCrawlError(Exception):
    """Raised when a crawl should be retried by RQ."""
    pass

class CrawlCancelledError(Exception):
    """Raised when a crawl has been cancelled."""
    pass

class CrawlTimeoutError(RetryableCrawlError):
    """Raised when an individual request times out (retryable)."""
    pass

class ResourceLimitError(Exception):
    """Raised when a response exceeds the maximum allowed size."""
    pass

class CrawlTimedOutError(Exception):
    """Raised when a CrawlJob exceeds its overall duration limit."""
    pass