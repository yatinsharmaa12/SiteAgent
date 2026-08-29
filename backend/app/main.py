from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.crawl import router as crawl_router
from app.api.company import router as company_router

app = FastAPI(title="AI Company Agent")
app.include_router(auth_router)
app.include_router(crawl_router)
app.include_router(chat_router)
app.include_router(company_router)

@app.get("/health")
def health():
    return {"status": "ok"}