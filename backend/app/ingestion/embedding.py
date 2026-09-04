from threading import Lock

from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

_shared_model = None
_shared_lock = Lock()


def _get_shared_model():
    global _shared_model
    if _shared_model is None:
        with _shared_lock:
            if _shared_model is None:
                _shared_model = SentenceTransformer(MODEL_NAME)
    return _shared_model


class EmbeddingModel:
    def __init__(self):
        # Shared singleton: loading takes seconds + ~100MB. Never reload
        # per chat/crawl request (resource exhaustion).
        self.model = _get_shared_model()

    def embed(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts).tolist()