from fastapi import FastAPI

from app.api.crawl import router as crawl_router


app = FastAPI(title="AI Company Agent")

app.include_router(crawl_router)


@app.get("/health")
def health():
    return {"status": "ok"}