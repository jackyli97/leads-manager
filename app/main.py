from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models
from app.database import engine
from app.routes.lead_routes import router as lead_router
from app.routes.routes import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(lead_router)


@app.get("/health")
def health():
    return {"status": "ok"}
