from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.config import Settings, get_settings
from ide_api.domains.documents.extraction import (
    extract_document_text,
    render_scanned_pdf_pages,
)
from ide_api.domains.documents.models import Document
from ide_api.domains.documents.service import DocumentService
from ide_api.domains.evidence.models import DocumentEvidenceLink
from ide_api.domains.evidence.service import EvidenceService
from ide_api.domains.impacts.models import DocumentRelationship, RelationshipAnalysisRun
from ide_api.domains.impacts.repository import ImpactRepository
from ide_api.domains.impacts.schemas import CandidateStatus
from ide_api.infrastructure.object_storage import ObjectStorage
from ide_api.infrastructure.openai import (
    DocumentAnalysisInput,
    EvidenceAnalysisInput,
    OpenAIRelationshipAnalyzer,
)


class RelationshipAnalysisService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        storage: ObjectStorage | None = None,
        analyzer: OpenAIRelationshipAnalyzer | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._storage = storage or ObjectStorage()
        self._analyzer = analyzer
        self._documents = DocumentService(session, self._storage, self._settings)
        self._evidence = EvidenceService(session, self._storage)
        self._impacts = ImpactRepository(session)

    async def queue_registered_document(self, *, document_id: UUID) -> UUID:
        source_document = await self._documents.get_relationship_analysis_source(
            document_id=document_id
        )
        source_version = source_document.versions[0]
        existing_run = await self._impacts.get_analysis_run(
            source_document_version_id=source_version.id,
            prompt_version=self._settings.openai_relationship_prompt_version,
        )
        if existing_run is not None:
            return existing_run.id

        run = RelationshipAnalysisRun(
            source_document_id=document_id,
            source_document_version_id=source_version.id,
            status="queued",
            prompt_version=self._settings.openai_relationship_prompt_version,
        )
        self._impacts.add_analysis_run(run)
        await self._session.commit()
        return run.id

    async def list_queued_document_ids(self) -> list[UUID]:
        return await self._impacts.list_queued_analysis_document_ids()

    async def analyze_registered_document(self, *, document_id: UUID) -> UUID:
        source_document = await self._documents.get_relationship_analysis_source(
            document_id=document_id
        )
        source_version = source_document.versions[0]
        existing_run = await self._impacts.get_analysis_run(
            source_document_version_id=source_version.id,
            prompt_version=self._settings.openai_relationship_prompt_version,
            for_update=True,
        )
        if existing_run is not None and existing_run.status in {"running", "completed"}:
            await self._session.commit()
            return existing_run.id

        run = existing_run or RelationshipAnalysisRun(
            source_document_id=document_id,
            source_document_version_id=source_version.id,
            status="running",
            prompt_version=self._settings.openai_relationship_prompt_version,
        )
        if existing_run is None:
            self._impacts.add_analysis_run(run)
        else:
            run.status = "running"
            run.error_message = None
        await self._session.commit()

        try:
            source = await self._document_input(source_document)
            other_documents = await self._documents.list_relationship_analysis_sources(
                exclude_document_id=document_id
            )
            document_inputs = [
                await self._document_input(document) for document in other_documents
            ]
            evidence_items = await self._evidence.list_evidence_items()
            evidence_inputs = [
                EvidenceAnalysisInput(
                    id=item.id,
                    evidence_type=item.evidence_type,
                    title=item.title,
                    description=item.description,
                    reference=item.reference,
                    location=item.location,
                    version=item.version,
                )
                for item in evidence_items
            ]
            analyzer = self._analyzer or OpenAIRelationshipAnalyzer(settings=self._settings)
            model = analyzer.route_model(
                source=source, documents=document_inputs, evidence=evidence_inputs
            )
            analyses = [
                await analyzer.analyze(
                    source=source,
                    documents=document_batch,
                    evidence=evidence_batch,
                    model=model,
                )
                for document_batch, evidence_batch in self._analysis_batches(
                    document_inputs, evidence_inputs
                )
            ]

            document_ids = {item.id for item in document_inputs}
            evidence_ids = {item.id for item in evidence_inputs}
            seen_document_suggestions: set[tuple[UUID, str, str, str]] = set()
            seen_evidence_suggestions: set[UUID] = set()
            for analysis in analyses:
                for suggestion in analysis.result.document_relationships:
                    key = (
                        suggestion.target_document_id,
                        suggestion.source_location,
                        suggestion.target_location,
                        suggestion.relationship_type,
                    )
                    if (
                        suggestion.target_document_id not in document_ids
                        or key in seen_document_suggestions
                    ):
                        continue
                    seen_document_suggestions.add(key)
                    self._impacts.add(
                        DocumentRelationship(
                            source_document_id=document_id,
                            source_location=suggestion.source_location,
                            target_document_id=suggestion.target_document_id,
                            target_location=suggestion.target_location,
                            relationship_type=suggestion.relationship_type,
                            reason=suggestion.reason,
                            status=CandidateStatus.CANDIDATE.value,
                            analysis_run_id=run.id,
                        )
                    )
                for suggestion in analysis.result.evidence_relationships:
                    if (
                        suggestion.evidence_id not in evidence_ids
                        or suggestion.evidence_id in seen_evidence_suggestions
                    ):
                        continue
                    seen_evidence_suggestions.add(suggestion.evidence_id)
                    self._session.add(
                        DocumentEvidenceLink(
                            document_id=document_id,
                            evidence_id=suggestion.evidence_id,
                            status="candidate",
                            freshness="current",
                            reason=suggestion.reason,
                            analysis_run_id=run.id,
                        )
                    )

            run.status = "completed"
            run.model_id = analyses[0].model_id
            run.completed_at = datetime.now(UTC)
            await self._session.commit()
            return run.id
        except Exception as error:
            await self._session.rollback()
            run = await self._impacts.get_analysis_run(
                source_document_version_id=source_version.id,
                prompt_version=self._settings.openai_relationship_prompt_version,
            )
            if run is not None:
                run.status = "failed"
                run.error_message = str(error)[:2000]
                run.completed_at = datetime.now(UTC)
                await self._session.commit()
            raise

    async def _document_input(self, document: Document) -> DocumentAnalysisInput:
        content, filename, _, resources = await self._documents.get_original(document.id)
        try:
            data = content.read()
        finally:
            resources.close()
        return DocumentAnalysisInput(
            id=document.id,
            filename=filename,
            content=extract_document_text(data, filename),
            page_images=(
                render_scanned_pdf_pages(data) if filename.lower().endswith(".pdf") else ()
            ),
        )

    @staticmethod
    def _analysis_batches(
        documents: list[DocumentAnalysisInput],
        evidence: list[EvidenceAnalysisInput],
    ) -> list[tuple[list[DocumentAnalysisInput], list[EvidenceAnalysisInput]]]:
        maximum_candidates = 20
        maximum_characters = 250_000
        maximum_images = 30
        batches: list[tuple[list[DocumentAnalysisInput], list[EvidenceAnalysisInput]]] = []
        document_batch: list[DocumentAnalysisInput] = []
        evidence_batch: list[EvidenceAnalysisInput] = []
        characters = 0
        images = 0

        def flush() -> None:
            nonlocal document_batch, evidence_batch, characters, images
            if document_batch or evidence_batch:
                batches.append((document_batch, evidence_batch))
            document_batch = []
            evidence_batch = []
            characters = 0
            images = 0

        for document in documents:
            candidate_count = len(document_batch) + len(evidence_batch)
            if (
                candidate_count >= maximum_candidates
                or (
                    candidate_count
                    and characters + len(document.content) > maximum_characters
                )
                or (candidate_count and images + len(document.page_images) > maximum_images)
            ):
                flush()
            document_batch.append(document)
            characters += len(document.content)
            images += len(document.page_images)

        for item in evidence:
            candidate_count = len(document_batch) + len(evidence_batch)
            if (
                candidate_count >= maximum_candidates
                or (
                    candidate_count
                    and characters + len(item.description) > maximum_characters
                )
            ):
                flush()
            evidence_batch.append(item)
            characters += len(item.description)

        flush()
        return batches or [([], [])]
