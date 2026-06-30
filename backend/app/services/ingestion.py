import uuid
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    ChunkEmbedding,
    Document,
    DocumentChunk,
    DocumentVersion,
    IngestionLog,
)
from app.models.enums import DocumentStatus, ExtractionStatus, LogStatus
from app.services.embeddings import get_embedding_provider
from app.services.storage import write_private_file

settings = get_settings()


@dataclass
class ExtractedSegment:
    content: str
    page_number: int | None
    section_title: str | None
    metadata: dict[str, object]


@dataclass
class ChunkPayload:
    chunk_index: int
    page_number: int | None
    section_title: str | None
    content: str
    token_count: int
    metadata: dict[str, object]


def create_ingestion_log(
    db: Session,
    *,
    document_version_id: uuid.UUID,
    step: str,
    status: LogStatus,
    message: str | None = None,
    details: dict[str, object] | None = None,
) -> IngestionLog:
    log = IngestionLog(
        document_version_id=document_version_id,
        step=step,
        status=status,
        message=message,
        details=details,
    )
    db.add(log)
    return log


def extract_segments_from_path(path_value: str) -> list[ExtractedSegment]:
    source_path = Path(path_value)
    suffix = source_path.suffix.lower()
    if suffix == ".txt":
        return _extract_text_segments(source_path)
    if suffix == ".pdf":
        return _extract_pdf_segments(source_path)
    raise ValueError(f"Unsupported document format for ingestion: {suffix}")


def build_chunks(segments: list[ExtractedSegment]) -> list[ChunkPayload]:
    if not segments:
        return []

    chunk_size = max(settings.ingestion_chunk_size_words, 1)
    chunk_overlap = max(min(settings.ingestion_chunk_overlap_words, chunk_size - 1), 0)
    chunks: list[ChunkPayload] = []
    chunk_index = 0

    for segment in segments:
        words = segment.content.split()
        if not words:
            continue

        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            content = " ".join(words[start:end]).strip()
            if content:
                chunks.append(
                    ChunkPayload(
                        chunk_index=chunk_index,
                        page_number=segment.page_number,
                        section_title=segment.section_title,
                        content=content,
                        token_count=len(content.split()),
                        metadata={
                            **segment.metadata,
                            "start_word": start,
                            "end_word": end,
                            "char_count": len(content),
                        },
                    )
                )
                chunk_index += 1

            if end >= len(words):
                break
            start = end - chunk_overlap

    return chunks


def process_document_version(document_version_id: uuid.UUID | str) -> dict[str, object]:
    from app.db.session import SessionLocal

    version_uuid = _normalize_uuid(document_version_id)
    with SessionLocal() as db:
        version = db.get(DocumentVersion, version_uuid)
        if version is None:
            return {
                "document_version_id": str(version_uuid),
                "status": "skipped",
                "reason": "document_version_not_found",
            }

        document = db.get(Document, version.document_id)
        if document is None:
            create_ingestion_log(
                db,
                document_version_id=version.id,
                step="failed",
                status=LogStatus.FAILED,
                message=(
                    "Ingestion could not continue because the document record "
                    "is missing."
                ),
                details={"document_id": str(version.document_id)},
            )
            version.extraction_status = ExtractionStatus.FAILED
            db.commit()
            return {
                "document_version_id": str(version.id),
                "status": DocumentStatus.FAILED.value,
                "error": f"Document {version.document_id} was not found",
            }

        document.status = DocumentStatus.PROCESSING
        version.extraction_status = ExtractionStatus.PROCESSING
        create_ingestion_log(
            db,
            document_version_id=version.id,
            step="processing",
            status=LogStatus.STARTED,
            message="Ingestion worker started processing the document version.",
        )
        db.commit()

        try:
            segments = extract_segments_from_path(version.file_path)
            if not segments:
                raise ValueError(
                    "No extractable text was found in the uploaded document."
                )

            extracted_text = "\n\n".join(
                segment.content for segment in segments
            ).strip()
            extracted_text_path = _write_extracted_text(
                version_id=version.id,
                file_name=version.file_name,
                extracted_text=extracted_text,
            )

            version.extracted_text_path = str(extracted_text_path)
            create_ingestion_log(
                db,
                document_version_id=version.id,
                step="extract",
                status=LogStatus.SUCCESS,
                message="Text extraction completed successfully.",
                details={
                    "segments": len(segments),
                    "extracted_text_path": str(extracted_text_path),
                },
            )
            db.commit()

            chunks = build_chunks(segments)
            if not chunks:
                raise ValueError("Chunking produced no usable content.")

            chunk_records = _replace_version_chunks(
                db,
                document=document,
                version=version,
                chunks=chunks,
            )
            create_ingestion_log(
                db,
                document_version_id=version.id,
                step="chunk",
                status=LogStatus.SUCCESS,
                message="Document chunks were stored successfully.",
                details={
                    "chunk_count": len(chunks),
                    "chunk_size_words": settings.ingestion_chunk_size_words,
                    "chunk_overlap_words": settings.ingestion_chunk_overlap_words,
                },
            )
            db.commit()

            embedding_provider = get_embedding_provider()
            embedding_result = embedding_provider.embed_texts(
                [chunk.content for chunk in chunk_records]
            )
            _store_chunk_embeddings(
                db,
                chunk_records=chunk_records,
                embedding_model=embedding_result.model,
                vectors=embedding_result.vectors,
            )
            create_ingestion_log(
                db,
                document_version_id=version.id,
                step="embed",
                status=LogStatus.SUCCESS,
                message="Chunk embeddings were stored successfully.",
                details={
                    "embedding_count": len(embedding_result.vectors),
                    "embedding_model": embedding_result.model,
                    "embedding_provider": embedding_result.provider,
                },
            )

            version.extraction_status = ExtractionStatus.PROCESSED
            document.status = DocumentStatus.PROCESSED
            create_ingestion_log(
                db,
                document_version_id=version.id,
                step="complete",
                status=LogStatus.SUCCESS,
                message="Ingestion completed successfully.",
            )
            db.commit()
            return {
                "document_version_id": str(version.id),
                "document_id": str(document.id),
                "status": DocumentStatus.PROCESSED.value,
                "chunk_count": len(chunks),
                "embedding_count": len(embedding_result.vectors),
                "embedding_model": embedding_result.model,
            }
        except Exception as exc:
            db.rollback()
            version = db.get(DocumentVersion, version_uuid)
            document = db.get(Document, version.document_id) if version else None
            if version is not None:
                version.extraction_status = ExtractionStatus.FAILED
            if document is not None:
                document.status = DocumentStatus.FAILED
            if version is not None:
                create_ingestion_log(
                    db,
                    document_version_id=version.id,
                    step="failed",
                    status=LogStatus.FAILED,
                    message="Ingestion failed.",
                    details={"error": str(exc)},
                )
            db.commit()
            return {
                "document_version_id": str(version_uuid),
                "status": DocumentStatus.FAILED.value,
                "error": str(exc),
            }


def _normalize_uuid(value: uuid.UUID | str) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _extract_text_segments(path_value: Path) -> list[ExtractedSegment]:
    text = path_value.read_text(encoding="utf-8", errors="replace")
    return _segments_from_plain_text(text)


def _extract_pdf_segments(path_value: Path) -> list[ExtractedSegment]:
    reader = PdfReader(str(path_value))
    segments: list[ExtractedSegment] = []
    for index, page in enumerate(reader.pages, start=1):
        page_text = _clean_text(page.extract_text() or "")
        if not page_text:
            continue
        segments.append(
            ExtractedSegment(
                content=page_text,
                page_number=index,
                section_title=None,
                metadata={"source": "pdf", "page_number": index},
            )
        )
    return segments


def _segments_from_plain_text(text: str) -> list[ExtractedSegment]:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    segments: list[ExtractedSegment] = []
    current_section: str | None = None
    current_lines: list[str] = []

    def flush_segment() -> None:
        nonlocal current_lines
        content = _clean_text("\n".join(current_lines))
        if content:
            segments.append(
                ExtractedSegment(
                    content=content,
                    page_number=None,
                    section_title=current_section,
                    metadata={"source": "text"},
                )
            )
        current_lines = []

    for raw_line in cleaned.split("\n"):
        line = raw_line.strip()
        if not line:
            flush_segment()
            continue

        heading = _detect_section_title(line)
        if heading is not None:
            flush_segment()
            current_section = heading
            continue

        current_lines.append(line)

    flush_segment()
    return segments


def _detect_section_title(line: str) -> str | None:
    if line.startswith("#"):
        return line.lstrip("#").strip() or None
    if line.endswith(":") and len(line.split()) <= 8:
        return line.rstrip(":").strip() or None
    if line.isupper() and len(line.split()) <= 8:
        return line.strip() or None
    return None


def _clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _write_extracted_text(
    *,
    version_id: uuid.UUID,
    file_name: str,
    extracted_text: str,
) -> Path:
    text_name = f"{Path(file_name).stem}.extracted.txt"
    return write_private_file(
        Path("extracted") / str(version_id) / text_name,
        extracted_text.encode("utf-8"),
    )


def _replace_version_chunks(
    db: Session,
    *,
    document: Document,
    version: DocumentVersion,
    chunks: list[ChunkPayload],
) -> list[DocumentChunk]:
    existing_chunk_ids = list(
        db.scalars(
            select(DocumentChunk.id).where(
                DocumentChunk.document_version_id == version.id
            )
        )
    )
    if existing_chunk_ids:
        db.execute(
            delete(ChunkEmbedding).where(
                ChunkEmbedding.chunk_id.in_(existing_chunk_ids)
            )
        )
        db.execute(
            delete(DocumentChunk).where(DocumentChunk.id.in_(existing_chunk_ids))
        )

    chunk_records: list[DocumentChunk] = []
    for chunk in chunks:
        chunk_record = DocumentChunk(
            workspace_id=document.workspace_id,
            document_id=document.id,
            document_version_id=version.id,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            section_title=chunk.section_title,
            content=chunk.content,
            token_count=chunk.token_count,
            metadata_json=chunk.metadata,
        )
        db.add(chunk_record)
        chunk_records.append(chunk_record)
    db.flush()
    return chunk_records


def _store_chunk_embeddings(
    db: Session,
    *,
    chunk_records: list[DocumentChunk],
    embedding_model: str,
    vectors: list[list[float]],
) -> None:
    if len(chunk_records) != len(vectors):
        raise ValueError(
            "Embedding vector count does not match the number of chunk records."
        )

    for chunk_record, vector in zip(chunk_records, vectors, strict=True):
        db.add(
            ChunkEmbedding(
                chunk_id=chunk_record.id,
                embedding_model=embedding_model,
                embedding=vector,
            )
        )
    db.flush()
