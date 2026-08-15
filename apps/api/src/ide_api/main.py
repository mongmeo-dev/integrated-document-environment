from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ide_api.config import get_settings
from ide_api.schemas import HealthResponse

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get(
    "/api/v1/health",
    operation_id="getHealth",
    response_model=HealthResponse,
    tags=["system"],
)
async def get_health() -> HealthResponse:
    return HealthResponse(status="ok")
