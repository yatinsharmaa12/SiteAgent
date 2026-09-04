import os

from dotenv import load_dotenv

load_dotenv()


MAX_RESPONSE_SIZE_BYTES = int(os.getenv("MAX_RESPONSE_SIZE_BYTES", "5000000"))  # 5 MiB
REQUEST_CONNECT_TIMEOUT = float(os.getenv("REQUEST_CONNECT_TIMEOUT", "10"))
REQUEST_READ_TIMEOUT = float(os.getenv("REQUEST_READ_TIMEOUT", "10"))
REQUEST_WRITE_TIMEOUT = float(os.getenv("REQUEST_WRITE_TIMEOUT", "10"))
REQUEST_POOL_TIMEOUT = float(os.getenv("REQUEST_POOL_TIMEOUT", "10"))
MAX_CRAWL_DURATION_SECONDS = int(os.getenv("MAX_CRAWL_DURATION_SECONDS", "1800"))  # 30 min
DOMAIN_MIN_DELAY_SECONDS = float(os.getenv("DOMAIN_MIN_DELAY_SECONDS", "1"))


JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def _parse_origins(raw: str) -> list:
    return [o.strip() for o in raw.split(",") if o.strip()]


CORS_ALLOW_ORIGINS = _parse_origins(
    os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
)
