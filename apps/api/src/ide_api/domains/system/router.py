from fastapi import APIRouter

from ide_api.domains.system.schemas import HealthResponse

router = APIRouter(tags=["system"])


@router.get(
    "/health",
    operation_id="getHealth",
    response_model=HealthResponse,
)
async def get_health() -> HealthResponse:
    return HealthResponse(status="ok")
