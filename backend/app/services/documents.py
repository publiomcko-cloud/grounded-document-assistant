import hashlib
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    ChunkEmbedding,
    Document,
    DocumentChunk,
    DocumentVersion,
    IngestionLog,
    MessageCitation,
    User,
    WorkspaceMembership,
)
from app.models.enums import (
    DocumentStatus,
    DocumentVisibility,
    ExtractionStatus,
    LogStatus,
    WorkspaceRole,
)
from app.services.ingestion import create_ingestion_log
from app.services.storage import (
    read_private_text_file,
    remove_directory_if_present,
    write_private_file,
)
from app.workers.queue import enqueue_document_ingestion

settings = get_settings()

ALLOWED_CONTENT_TYPES = {
    ".pdf": {"application/pdf"},
    ".txt": {"text/plain"},
}

UPLOAD_DOCUMENT_ROLES = {
    WorkspaceRole.OWNER,
    WorkspaceRole.ADMIN,
    WorkspaceRole.MEMBER,
}

MANAGE_DOCUMENT_ROLES = {
    WorkspaceRole.OWNER,
    WorkspaceRole.ADMIN,
}


@dataclass
class DocumentContext:
    document: Document
    versions: list[DocumentVersion]
    latest_version_logs: list[IngestionLog] = field(default_factory=list)
    latest_version_chunks: list[DocumentChunk] = field(default_factory=list)
    latest_version_chunk_count: int = 0
    latest_version_embedding_count: int = 0
    latest_version_extracted_text: str | None = None


def normalize_visibility(value: str) -> DocumentVisibility:
    try:
        return DocumentVisibility(value)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in DocumentVisibility)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid visibility. Expected one of: {allowed}",
        ) from exc


async def validate_upload(file: UploadFile) -> tuple[str, bytes]:
    filename = file.filename or "upload"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and plain text files are supported",
        )

    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES[suffix]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file type does not match the supported format",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds the {settings.max_upload_mb} MB upload limit",
        )

    return suffix, content


def require_upload_permission(membership: WorkspaceMembership) -> None:
    if membership.role not in UPLOAD_DOCUMENT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to upload documents",
        )


def require_manage_permission(membership: WorkspaceMembership) -> None:
    if membership.role not in MANAGE_DOCUMENT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage documents",
        )


async def create_document_with_version(
    db: Session,
    *,
    membership: WorkspaceMembership,
    user: User,
    title: str,
    description: str | None,
    visibility: DocumentVisibility,
    file: UploadFile,
) -> DocumentContext:
    require_upload_permission(membership)

    normalized_title = title.strip()
    if not normalized_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document title is required",
        )

    suffix, content = await validate_upload(file)

    document = Document(
        workspace_id=membership.workspace_id,
        title=normalized_title,
        description=description.strip() if description else None,
        status=DocumentStatus.PENDING,
        visibility=visibility,
        uploaded_by_user_id=user.id,
    )
    db.add(document)
    db.flush()

    version_id = uuid.uuid4()
    version_root = (
        Path(str(membership.workspace_id))
        / "documents"
        / str(document.id)
        / str(version_id)
    )
    filename = file.filename or f"document{suffix}"
    stored_path = write_private_file(version_root / filename, content)

    version = DocumentVersion(
        id=version_id,
        document_id=document.id,
        version_number=1,
        file_name=filename,
        file_path=str(stored_path),
        mime_type=file.content_type or next(iter(ALLOWED_CONTENT_TYPES[suffix])),
        file_size_bytes=len(content),
        checksum=hashlib.sha256(content).hexdigest(),
        extraction_status=ExtractionStatus.PENDING,
    )
    db.add(version)
    db.commit()
    db.refresh(document)

    try:
        enqueue_document_ingestion(
            db,
            document_version_id=version.id,
            trigger="upload",
        )
        db.refresh(document)
        db.refresh(version)
    except Exception as exc:
        document.status = DocumentStatus.FAILED
        version.extraction_status = ExtractionStatus.FAILED
        create_ingestion_log(
            db,
            document_version_id=version.id,
            step="failed",
            status=LogStatus.FAILED,
            message=(
                "Document upload succeeded, but the ingestion job could not be queued."
            ),
            details={"error": str(exc)},
        )
        db.commit()
        db.refresh(document)
        db.refresh(version)

    return _build_document_context(
        db,
        document=document,
        versions=[version],
    )


def list_workspace_documents(
    db: Session,
    *,
    workspace_id: uuid.UUID,
) -> list[DocumentContext]:
    documents = list(
        db.scalars(
            select(Document)
            .where(Document.workspace_id == workspace_id)
            .order_by(Document.created_at.desc())
        )
    )
    if not documents:
        return []

    versions = list(
        db.scalars(
            select(DocumentVersion)
            .where(DocumentVersion.document_id.in_([doc.id for doc in documents]))
            .order_by(
                DocumentVersion.document_id, DocumentVersion.version_number.desc()
            )
        )
    )
    versions_by_document: dict[uuid.UUID, list[DocumentVersion]] = {}
    for version in versions:
        versions_by_document.setdefault(version.document_id, []).append(version)

    return [
        _build_document_context(
            db,
            document=document,
            versions=versions_by_document.get(document.id, []),
            include_latest_details=False,
        )
        for document in documents
    ]


def get_workspace_document(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
) -> DocumentContext:
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.workspace_id == workspace_id,
        )
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    versions = list(
        db.scalars(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document.id)
            .order_by(DocumentVersion.version_number.desc())
        )
    )
    return _build_document_context(
        db,
        document=document,
        versions=versions,
    )


def disable_workspace_document(
    db: Session,
    *,
    membership: WorkspaceMembership,
    document_id: uuid.UUID,
) -> DocumentContext:
    require_manage_permission(membership)
    context = get_workspace_document(
        db,
        workspace_id=membership.workspace_id,
        document_id=document_id,
    )
    context.document.status = DocumentStatus.DISABLED
    db.commit()
    db.refresh(context.document)
    return get_workspace_document(
        db,
        workspace_id=membership.workspace_id,
        document_id=document_id,
    )


def retry_workspace_document_ingestion(
    db: Session,
    *,
    membership: WorkspaceMembership,
    document_id: uuid.UUID,
) -> DocumentContext:
    require_manage_permission(membership)
    context = get_workspace_document(
        db,
        workspace_id=membership.workspace_id,
        document_id=document_id,
    )
    if not context.versions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no version available for retry",
        )

    latest_version = context.versions[0]
    context.document.status = DocumentStatus.PENDING
    latest_version.extraction_status = ExtractionStatus.PENDING
    db.commit()

    try:
        enqueue_document_ingestion(
            db,
            document_version_id=latest_version.id,
            trigger="retry",
        )
    except Exception as exc:
        context.document.status = DocumentStatus.FAILED
        latest_version.extraction_status = ExtractionStatus.FAILED
        create_ingestion_log(
            db,
            document_version_id=latest_version.id,
            step="failed",
            status=LogStatus.FAILED,
            message="Retry requested, but the ingestion job could not be queued.",
            details={"error": str(exc)},
        )
        db.commit()

    db.expire_all()
    return get_workspace_document(
        db,
        workspace_id=membership.workspace_id,
        document_id=document_id,
    )


def delete_workspace_document(
    db: Session,
    *,
    membership: WorkspaceMembership,
    document_id: uuid.UUID,
) -> None:
    require_manage_permission(membership)
    context = get_workspace_document(
        db,
        workspace_id=membership.workspace_id,
        document_id=document_id,
    )

    for version in context.versions:
        remove_directory_if_present(Path(version.file_path).parent)
        remove_directory_if_present(
            Path(version.extracted_text_path).parent
            if version.extracted_text_path
            else None
        )

    chunk_ids = list(
        db.scalars(
            select(DocumentChunk.id).where(DocumentChunk.document_id == document_id)
        )
    )
    if chunk_ids:
        db.execute(delete(ChunkEmbedding).where(ChunkEmbedding.chunk_id.in_(chunk_ids)))
        db.execute(
            delete(MessageCitation).where(MessageCitation.chunk_id.in_(chunk_ids))
        )
        db.execute(delete(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids)))

    version_ids = [version.id for version in context.versions]
    if version_ids:
        db.execute(
            delete(IngestionLog).where(
                IngestionLog.document_version_id.in_(version_ids)
            )
        )

    db.execute(
        delete(MessageCitation).where(MessageCitation.document_id == document_id)
    )
    db.execute(
        delete(DocumentVersion).where(DocumentVersion.document_id == document_id)
    )
    db.execute(delete(Document).where(Document.id == document_id))
    db.commit()


def _build_document_context(
    db: Session,
    *,
    document: Document,
    versions: list[DocumentVersion],
    include_latest_details: bool = True,
) -> DocumentContext:
    if not versions or not include_latest_details:
        return DocumentContext(document=document, versions=versions)

    latest_version = versions[0]
    latest_version_logs = list(
        db.scalars(
            select(IngestionLog)
            .where(IngestionLog.document_version_id == latest_version.id)
            .order_by(IngestionLog.created_at.desc())
        )
    )
    latest_version_chunks = list(
        db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_version_id == latest_version.id)
            .order_by(DocumentChunk.chunk_index.asc())
            .limit(5)
        )
    )
    return DocumentContext(
        document=document,
        versions=versions,
        latest_version_logs=latest_version_logs,
        latest_version_chunks=latest_version_chunks,
        latest_version_chunk_count=db.scalar(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_version_id == latest_version.id
            )
        )
        or 0,
        latest_version_embedding_count=db.scalar(
            select(func.count(ChunkEmbedding.id))
            .join(DocumentChunk, DocumentChunk.id == ChunkEmbedding.chunk_id)
            .where(DocumentChunk.document_version_id == latest_version.id)
        )
        or 0,
        latest_version_extracted_text=read_private_text_file(
            latest_version.extracted_text_path
        ),
    )
