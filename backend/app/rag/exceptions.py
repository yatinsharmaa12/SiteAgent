from typing import Optional


class LLMProviderError(Exception):
    """Application-level error for an unavailable language-model provider."""

    def __init__(self, message: str, provider_status_code: Optional[int] = None):
        super().__init__(message)
        self.provider_status_code = provider_status_code
