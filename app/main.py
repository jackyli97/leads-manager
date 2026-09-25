from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import models
from app.database import engine
from app.routes.lead_routes import router as lead_router
from app.routes.routes import router as auth_router
from app.services.storage import UPLOAD_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(lead_router)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR, check_dir=False), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}
