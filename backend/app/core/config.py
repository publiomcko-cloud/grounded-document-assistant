from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://app:app@localhost:5433/grounded_document_assistant"
    )
    redis_url: str | None = None
    redis_host: str | None = None
    redis_port: int = 6379
    app_env: str = "development"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:3001,"
        "http://127.0.0.1:3001"
    )
    file_storage_path: str = "./storage"
    max_upload_mb: int = 25
    ingestion_chunk_size_words: int = 180
    ingestion_chunk_overlap_words: int = 30
    ingestion_queue_name: str = "grounded-document-assistant-ingestion"
    ingestion_job_timeout_seconds: int = 600
    ingestion_queue_eager: bool = False
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_provider: str = "local"
    chat_model: str = "local-grounded-answerer"
    embedding_provider: str = "local"
    embedding_model: str = "local-hash-1536"
    embedding_api_key: str | None = None
    embedding_base_url: str | None = None
    embedding_request_timeout_seconds: int = 30
    retrieval_top_k_default: int = 5
    answer_max_citations: int = 3

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def redis_connection_url(self) -> str:
        if self.redis_url:
            return self.redis_url
        if self.redis_host:
            return f"redis://{self.redis_host}:{self.redis_port}"
        return "redis://localhost:6379"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
