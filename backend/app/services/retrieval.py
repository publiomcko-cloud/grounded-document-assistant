from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models import ChunkEmbedding, Document, DocumentChunk, DocumentVersion, User
from app.models.enums import (
    DocumentStatus,
    DocumentVisibility,
    ExtractionStatus,
    WorkspaceRole,
)
from app.schemas.retrieval import (
    RetrievalResultItem,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from app.services.embeddings import EmbeddingProviderError, get_embedding_provider

VECTOR_FALLBACK_THRESHOLD = 0.55
RESTRICTED_ROLES = {
    WorkspaceRole.OWNER,
    WorkspaceRole.ADMIN,
    WorkspaceRole.MEMBER,
}
PRIVATE_ROLES = {
    WorkspaceRole.OWNER,
    WorkspaceRole.ADMIN,
}


@dataclass
class RetrievalCandidate:
    chunk: DocumentChunk
    document: Document
    score: float
    score_type: str


def search_workspace_chunks(
    db: Session,
    *,
    workspace_id: UUID,
    current_user: User,
    membership_role: WorkspaceRole,
    request: RetrievalSearchRequest,
) -> RetrievalSearchResponse:
    cleaned_query = request.query.strip()
    if not cleaned_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must not be empty",
        )

    vector_candidates: list[RetrievalCandidate] = []
    keyword_candidates: list[RetrievalCandidate] = []

    if request.strategy in {"vector", "hybrid"}:
        try:
            vector_candidates = _run_vector_search(
                db,
                workspace_id=workspace_id,
                current_user=current_user,
                membership_role=membership_role,
                query_text=cleaned_query,
                top_k=request.top_k,
                document_ids=request.document_ids,
            )
        except EmbeddingProviderError as exc:
            if request.strategy == "vector":
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Could not generate query embedding: {exc}",
                ) from exc

    if request.strategy == "keyword":
        keyword_candidates = _run_keyword_search(
            db,
            workspace_id=workspace_id,
            current_user=current_user,
            membership_role=membership_role,
            query_text=cleaned_query,
            top_k=request.top_k,
            document_ids=request.document_ids,
        )
        return _build_response(
            query=cleaned_query,
            strategy_requested=request.strategy,
            strategy_used="keyword",
            candidates=keyword_candidates,
        )

    if request.strategy == "vector":
        return _build_response(
            query=cleaned_query,
            strategy_requested=request.strategy,
            strategy_used="vector",
            candidates=vector_candidates,
        )

    use_keyword_fallback = (
        not vector_candidates or vector_candidates[0].score < VECTOR_FALLBACK_THRESHOLD
    )

    if use_keyword_fallback:
        keyword_candidates = _run_keyword_search(
            db,
            workspace_id=workspace_id,
            current_user=current_user,
            membership_role=membership_role,
            query_text=cleaned_query,
            top_k=request.top_k,
            document_ids=request.document_ids,
        )
        merged_candidates = _merge_candidates(
            primary=keyword_candidates,
            secondary=vector_candidates,
            top_k=request.top_k,
        )
        return _build_response(
            query=cleaned_query,
            strategy_requested=request.strategy,
            strategy_used="keyword_fallback",
            candidates=merged_candidates,
        )

    return _build_response(
        query=cleaned_query,
        strategy_requested=request.strategy,
        strategy_used="vector",
        candidates=vector_candidates[: request.top_k],
    )


def _run_vector_search(
    db: Session,
    *,
    workspace_id: UUID,
    current_user: User,
    membership_role: WorkspaceRole,
    query_text: str,
    top_k: int,
    document_ids: list[UUID] | None,
) -> list[RetrievalCandidate]:
    provider = get_embedding_provider()
    embedding_result = provider.embed_texts([query_text])
    query_vector = embedding_result.vectors[0]
    similarity = (1 - ChunkEmbedding.embedding.cosine_distance(query_vector)).label(
        "score"
    )

    stmt = (
        select(DocumentChunk, Document, similarity)
        .join(ChunkEmbedding, ChunkEmbedding.chunk_id == DocumentChunk.id)
        .join(Document, Document.id == DocumentChunk.document_id)
        .join(DocumentVersion, DocumentVersion.id == DocumentChunk.document_version_id)
        .where(
            *_base_retrieval_filters(
                workspace_id=workspace_id,
                current_user_id=current_user.id,
                membership_role=membership_role,
                document_ids=document_ids,
            ),
            DocumentVersion.extraction_status == ExtractionStatus.PROCESSED,
        )
        .order_by(similarity.desc(), DocumentChunk.chunk_index.asc())
        .limit(top_k)
    )
    rows = db.execute(stmt).all()
    return [
        RetrievalCandidate(
            chunk=row[0],
            document=row[1],
            score=float(row[2]),
            score_type="vector_similarity",
        )
        for row in rows
    ]


def _run_keyword_search(
    db: Session,
    *,
    workspace_id: UUID,
    current_user: User,
    membership_role: WorkspaceRole,
    query_text: str,
    top_k: int,
    document_ids: list[UUID] | None,
) -> list[RetrievalCandidate]:
    tsquery = func.plainto_tsquery("english", query_text)
    rank = func.ts_rank_cd(func.to_tsvector("english", DocumentChunk.content), tsquery)
    rank_label = rank.label("score")

    stmt = (
        select(DocumentChunk, Document, rank_label)
        .join(Document, Document.id == DocumentChunk.document_id)
        .join(DocumentVersion, DocumentVersion.id == DocumentChunk.document_version_id)
        .where(
            *_base_retrieval_filters(
                workspace_id=workspace_id,
                current_user_id=current_user.id,
                membership_role=membership_role,
                document_ids=document_ids,
            ),
            DocumentVersion.extraction_status == ExtractionStatus.PROCESSED,
            rank > 0,
        )
        .order_by(rank_label.desc(), DocumentChunk.chunk_index.asc())
        .limit(top_k)
    )
    rows = db.execute(stmt).all()
    return [
        RetrievalCandidate(
            chunk=row[0],
            document=row[1],
            score=float(row[2]),
            score_type="keyword_rank",
        )
        for row in rows
    ]


def _base_retrieval_filters(
    *,
    workspace_id: UUID,
    current_user_id: UUID,
    membership_role: WorkspaceRole,
    document_ids: list[UUID] | None,
) -> tuple[Any, ...]:
    visibility_filter = _visibility_filter(
        current_user_id=current_user_id,
        membership_role=membership_role,
    )
    filters: list[Any] = [
        DocumentChunk.workspace_id == workspace_id,
        Document.workspace_id == workspace_id,
        Document.status == DocumentStatus.PROCESSED,
        visibility_filter,
    ]
    if document_ids:
        filters.append(Document.id.in_(document_ids))
    return tuple(filters)


def _visibility_filter(
    *,
    current_user_id: UUID,
    membership_role: WorkspaceRole,
) -> Any:
    restricted_allowed = membership_role in RESTRICTED_ROLES
    private_allowed = membership_role in PRIVATE_ROLES

    conditions = [Document.visibility == DocumentVisibility.WORKSPACE]
    if restricted_allowed:
        conditions.append(Document.visibility == DocumentVisibility.RESTRICTED)
    if private_allowed:
        conditions.append(Document.visibility == DocumentVisibility.PRIVATE)
    else:
        conditions.append(
            and_(
                Document.visibility == DocumentVisibility.PRIVATE,
                Document.uploaded_by_user_id == current_user_id,
            )
        )

    return or_(*conditions)


def _merge_candidates(
    *,
    primary: list[RetrievalCandidate],
    secondary: list[RetrievalCandidate],
    top_k: int,
) -> list[RetrievalCandidate]:
    merged: dict[UUID, RetrievalCandidate] = {}
    for candidate in [*primary, *secondary]:
        existing = merged.get(candidate.chunk.id)
        if existing is None or candidate.score > existing.score:
            merged[candidate.chunk.id] = candidate
    return sorted(
        merged.values(),
        key=lambda item: item.score,
        reverse=True,
    )[:top_k]


def _build_response(
    *,
    query: str,
    strategy_requested: str,
    strategy_used: str,
    candidates: list[RetrievalCandidate],
) -> RetrievalSearchResponse:
    return RetrievalSearchResponse(
        query=query,
        strategy_requested=strategy_requested,
        strategy_used=strategy_used,
        total_results=len(candidates),
        results=[
            RetrievalResultItem(
                chunk_id=candidate.chunk.id,
                document_id=candidate.document.id,
                document_version_id=candidate.chunk.document_version_id,
                document_title=candidate.document.title,
                document_visibility=candidate.document.visibility,
                chunk_index=candidate.chunk.chunk_index,
                page_number=candidate.chunk.page_number,
                section_title=candidate.chunk.section_title,
                content=candidate.chunk.content,
                score=candidate.score,
                score_type=candidate.score_type,
            )
            for candidate in candidates
        ],
    )
