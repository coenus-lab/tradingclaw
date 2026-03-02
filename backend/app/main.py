from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.core.db import Base, engine

app = FastAPI(title=settings.app_name)
Base.metadata.create_all(bind=engine)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
