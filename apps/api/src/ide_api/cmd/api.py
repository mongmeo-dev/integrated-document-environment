from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ide_api.api.v1.router import router as api_v1_router
from ide_api.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(api_v1_router, prefix="/api/v1")
