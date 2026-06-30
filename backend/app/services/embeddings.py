import hashlib
import math
from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.models.entities import EMBEDDING_DIMENSIONS

settings = get_settings()


class EmbeddingProviderError(RuntimeError):
    pass


@dataclass
class EmbeddingResult:
    model: str
    vectors: list[list[float]]
    provider: str


class EmbeddingProvider:
    provider_name = "base"

    def embed_texts(self, texts: list[str]) -> EmbeddingResult:
        raise NotImplementedError


class LocalHashEmbeddingProvider(EmbeddingProvider):
    provider_name = "local"

    def embed_texts(self, texts: list[str]) -> EmbeddingResult:
        vectors = [_hash_to_unit_vector(text) for text in texts]
        return EmbeddingResult(
            model=settings.embedding_model,
            vectors=vectors,
            provider=self.provider_name,
        )


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    provider_name = "openai_compatible"

    def __init__(self) -> None:
        api_key = settings.embedding_api_key or settings.llm_api_key
        base_url = settings.embedding_base_url or settings.llm_base_url
        if not api_key or not base_url:
            raise EmbeddingProviderError(
                "OpenAI-compatible embeddings require EMBEDDING_API_KEY or "
                "LLM_API_KEY, plus EMBEDDING_BASE_URL or LLM_BASE_URL."
            )

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def embed_texts(self, texts: list[str]) -> EmbeddingResult:
        try:
            response = httpx.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.embedding_model,
                    "input": texts,
                },
                timeout=settings.embedding_request_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise EmbeddingProviderError(
                f"Embedding provider request failed: {exc}"
            ) from exc

        payload = response.json()
        data = payload.get("data")
        if not isinstance(data, list) or len(data) != len(texts):
            raise EmbeddingProviderError(
                "Embedding provider returned an unexpected response shape."
            )

        vectors: list[list[float]] = []
        for item in data:
            embedding = item.get("embedding")
            if not isinstance(embedding, list):
                raise EmbeddingProviderError(
                    "Embedding provider returned a non-list embedding."
                )
            if len(embedding) != EMBEDDING_DIMENSIONS:
                raise EmbeddingProviderError(
                    "Embedding vector dimension does not match the configured "
                    f"pgvector column size of {EMBEDDING_DIMENSIONS}."
                )
            vectors.append([float(value) for value in embedding])

        return EmbeddingResult(
            model=settings.embedding_model,
            vectors=vectors,
            provider=self.provider_name,
        )


def get_embedding_provider() -> EmbeddingProvider:
    provider = settings.embedding_provider.strip().lower()
    if provider == "local":
        return LocalHashEmbeddingProvider()
    if provider == "openai_compatible":
        return OpenAICompatibleEmbeddingProvider()
    raise EmbeddingProviderError(f"Unsupported embedding provider: {provider}")


def _hash_to_unit_vector(text: str) -> list[float]:
    values: list[float] = []
    counter = 0
    seed = text.strip() or " "

    while len(values) < EMBEDDING_DIMENSIONS:
        digest = hashlib.blake2b(
            f"{seed}:{counter}".encode("utf-8"),
            digest_size=32,
        ).digest()
        for index in range(0, len(digest), 4):
            if len(values) >= EMBEDDING_DIMENSIONS:
                break
            integer = int.from_bytes(digest[index : index + 4], "big")
            values.append((integer / 0xFFFFFFFF) * 2 - 1)
        counter += 1

    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]
