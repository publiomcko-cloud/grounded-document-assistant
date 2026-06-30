from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, Response, UploadFile, status

from app.api.dependencies.auth import CurrentUserDep, WorkspaceContextDep
from app.db.session import DBSessionDep
from app.models.enums import DocumentVisibility
from app.schemas.document import (
    DocumentChunkPreview,
    DocumentDetail,
    DocumentSummary,
    DocumentVersionSummary,
    IngestionLogEntry,
)
from app.services.documents import (
    create_document_with_version,
    delete_workspace_document,
    disable_workspace_document,
    get_workspace_document,
    list_workspace_documents,
    normalize_visibility,
    retry_workspace_document_ingestion,
)

router = APIRouter(prefix="/documents", tags=["documents"])


def serialize_document_summary(document, versions) -> DocumentSummary:
    latest_version = versions[0] if versions else None
    return DocumentSummary(
        **DocumentSummary.model_validate(document).model_dump(
            exclude={"latest_version"}
        ),
        latest_version=(
            DocumentVersionSummary.model_validate(latest_version)
            if latest_version
            else None
        ),
    )


def serialize_document_detail(document, versions) -> DocumentDetail:
    summary = serialize_document_summary(document, versions)
    return DocumentDetail(
        **summary.model_dump(),
        versions=[
            DocumentVersionSummary.model_validate(version) for version in versions
        ],
        latest_version_logs=[],
        latest_version_chunk_preview=[],
        latest_version_chunk_count=0,
        latest_version_embedding_count=0,
        latest_version_extracted_text=None,
    )


def serialize_document_context(context) -> DocumentDetail:
    summary = serialize_document_summary(context.document, context.versions)
    return DocumentDetail(
        **summary.model_dump(),
        versions=[
            DocumentVersionSummary.model_validate(version)
            for version in context.versions
        ],
        latest_version_logs=[
            IngestionLogEntry.model_validate(log) for log in context.latest_version_logs
        ],
        latest_version_chunk_preview=[
            DocumentChunkPreview.model_validate(chunk)
            for chunk in context.latest_version_chunks
        ],
        latest_version_chunk_count=context.latest_version_chunk_count,
        latest_version_embedding_count=context.latest_version_embedding_count,
        latest_version_extracted_text=context.latest_version_extracted_text,
    )


@router.get("", response_model=list[DocumentSummary])
def list_documents(
    workspace_context: WorkspaceContextDep,
    db: DBSessionDep,
) -> list[DocumentSummary]:
    contexts = list_workspace_documents(
        db,
        workspace_id=workspace_context.membership.workspace_id,
    )
    return [
        serialize_document_summary(context.document, context.versions)
        for context in contexts
    ]


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: UUID,
    workspace_context: WorkspaceContextDep,
    db: DBSessionDep,
) -> DocumentDetail:
    context = get_workspace_document(
        db,
        workspace_id=workspace_context.membership.workspace_id,
        document_id=document_id,
    )
    return serialize_document_context(context)


@router.post("", response_model=DocumentDetail, status_code=status.HTTP_201_CREATED)
async def upload_document(
    workspace_context: WorkspaceContextDep,
    current_user: CurrentUserDep,
    db: DBSessionDep,
    title: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    description: Annotated[str | None, Form()] = None,
    visibility: Annotated[str, Form()] = DocumentVisibility.WORKSPACE.value,
) -> DocumentDetail:
    context = await create_document_with_version(
        db,
        membership=workspace_context.membership,
        user=current_user,
        title=title,
        description=description,
        visibility=normalize_visibility(visibility),
        file=file,
    )
    return serialize_document_context(context)


@router.patch("/{document_id}/disable", response_model=DocumentDetail)
def disable_document(
    document_id: UUID,
    workspace_context: WorkspaceContextDep,
    db: DBSessionDep,
) -> DocumentDetail:
    context = disable_workspace_document(
        db,
        membership=workspace_context.membership,
        document_id=document_id,
    )
    return serialize_document_context(context)


@router.post("/{document_id}/retry", response_model=DocumentDetail)
def retry_document_ingestion(
    document_id: UUID,
    workspace_context: WorkspaceContextDep,
    db: DBSessionDep,
) -> DocumentDetail:
    context = retry_workspace_document_ingestion(
        db,
        membership=workspace_context.membership,
        document_id=document_id,
    )
    return serialize_document_context(context)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    workspace_context: WorkspaceContextDep,
    db: DBSessionDep,
) -> Response:
    delete_workspace_document(
        db,
        membership=workspace_context.membership,
        document_id=document_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
