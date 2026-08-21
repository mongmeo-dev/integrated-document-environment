import asyncio
from uuid import UUID

from ide_api.cmd.worker import app
from ide_api.config import get_settings
from ide_api.core.database import async_session, engine
from ide_api.domains.impacts.analysis import RelationshipAnalysisService


@app.task(
    name="ide_api.impacts.analyze_registered_document",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def analyze_registered_document(document_id: str) -> str:
    return asyncio.run(_analyze_registered_document(UUID(document_id)))


async def _analyze_registered_document(document_id: UUID) -> str:
    try:
        async with async_session() as session:
            run_id = await RelationshipAnalysisService(session).analyze_registered_document(
                document_id=document_id
            )
            return str(run_id)
    finally:
        await engine.dispose()


@app.task(name="ide_api.impacts.recover_queued_relationship_analyses")
def recover_queued_relationship_analyses() -> int:
    if not get_settings().openai_api_key:
        return 0
    document_ids = asyncio.run(_list_queued_analysis_document_ids())
    for document_id in document_ids:
        analyze_registered_document.delay(str(document_id))
    return len(document_ids)


async def _list_queued_analysis_document_ids() -> list[UUID]:
    try:
        async with async_session() as session:
            service = RelationshipAnalysisService(session)
            return await service.list_queued_document_ids()
    finally:
        await engine.dispose()


def enqueue_relationship_analysis(document_id: UUID) -> None:
    analyze_registered_document.apply_async(args=[str(document_id)], retry=False)
