from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.company import router as company_router
from app.api.company_crawl import router as company_crawl_router
from app.core.config import CORS_ALLOW_ORIGINS

app = FastAPI(title="AI Company Agent")

# Explicit allowlist (no "*"): Bearer-header auth needs no credentials mode,
# which keeps CSRF surface minimal. Prod must set CORS_ALLOW_ORIGINS to the
# exact web origin(s), e.g. "https://app.example.com".
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )
        # Ignored by browsers over plain http; enforced once behind https.
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        return response


# Added after CORS so it also stamps preflight/short-circuit responses.
app.add_middleware(SecurityHeadersMiddleware)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(company_router)
app.include_router(company_crawl_router)

@app.get("/health")
def health():
    return {"status": "ok"}