from app.services.ingestion import process_document_version


def run_document_ingestion(document_version_id: str) -> dict[str, object]:
    return process_document_version(document_version_id)
