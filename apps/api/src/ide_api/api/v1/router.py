from fastapi import APIRouter

from ide_api.domains.approvals.router import router as approvals_router
from ide_api.domains.auth.router import router as auth_router
from ide_api.domains.changes.router import router as changes_router
from ide_api.domains.completion.router import router as completion_router
from ide_api.domains.documents.router import router as documents_router
from ide_api.domains.evidence.router import router as evidence_router
from ide_api.domains.formatting.router import router as formatting_router
from ide_api.domains.history.router import router as history_router
from ide_api.domains.impacts.router import router as impacts_router
from ide_api.domains.system.router import router as system_router

router = APIRouter()
router.include_router(system_router)
router.include_router(auth_router)
router.include_router(documents_router)
router.include_router(changes_router)
router.include_router(impacts_router)
router.include_router(evidence_router)
router.include_router(formatting_router)
router.include_router(approvals_router)
router.include_router(completion_router)
router.include_router(history_router)
