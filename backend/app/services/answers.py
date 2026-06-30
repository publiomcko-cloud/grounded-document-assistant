import json
import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import ROOT_DIR, get_settings
from app.schemas.retrieval import RetrievalResultItem

settings = get_settings()
PROMPT_PATH = ROOT_DIR / "backend" / "app" / "prompts" / "grounded_answer_system.txt"
SAFE_INSUFFICIENT_CONTEXT_ANSWER = (
    "I do not have enough information in the available documents to answer that "
    "confidently."
)


class AnswerProviderError(RuntimeError):
    pass


@dataclass
class AnswerResult:
    answer: str
    insufficient_context: bool
    citation_chunk_ids: list[str]
    model_name: str
    token_usage: dict[str, Any] | None
    provider: str


class AnswerProvider:
    provider_name = "base"

    def generate_answer(
        self,
        *,
        question: str,
        retrieved_chunks: list[RetrievalResultItem],
    ) -> AnswerResult:
        raise NotImplementedError


class LocalGroundedAnswerProvider(AnswerProvider):
    provider_name = "local"

    def generate_answer(
        self,
        *,
        question: str,
        retrieved_chunks: list[RetrievalResultItem],
    ) -> AnswerResult:
        if not retrieved_chunks:
            return AnswerResult(
                answer=SAFE_INSUFFICIENT_CONTEXT_ANSWER,
                insufficient_context=True,
                citation_chunk_ids=[],
                model_name=settings.chat_model,
                token_usage={"provider": "local", "retrieved_chunks": 0},
                provider=self.provider_name,
            )

        ranked = _rank_chunks_for_answer(question=question, chunks=retrieved_chunks)
        chosen = ranked[: settings.answer_max_citations]
        summary_lines = []
        for chunk in chosen:
            snippet = _best_snippet_for_question(question, chunk.content)
            summary_lines.append(snippet)

        answer = " ".join(summary_lines).strip()
        if not answer:
            return AnswerResult(
                answer=SAFE_INSUFFICIENT_CONTEXT_ANSWER,
                insufficient_context=True,
                citation_chunk_ids=[],
                model_name=settings.chat_model,
                token_usage={
                    "provider": "local",
                    "retrieved_chunks": len(retrieved_chunks),
                },
                provider=self.provider_name,
            )

        return AnswerResult(
            answer=answer,
            insufficient_context=False,
            citation_chunk_ids=[str(chunk.chunk_id) for chunk in chosen],
            model_name=settings.chat_model,
            token_usage={
                "provider": "local",
                "retrieved_chunks": len(retrieved_chunks),
                "used_citations": len(chosen),
            },
            provider=self.provider_name,
        )


class OpenAICompatibleAnswerProvider(AnswerProvider):
    provider_name = "openai_compatible"

    def __init__(self) -> None:
        if not settings.llm_api_key or not settings.llm_base_url:
            raise AnswerProviderError(
                "OpenAI-compatible chat requires LLM_API_KEY and LLM_BASE_URL."
            )
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url.rstrip("/")
        self.system_prompt = load_answer_system_prompt()

    def generate_answer(
        self,
        *,
        question: str,
        retrieved_chunks: list[RetrievalResultItem],
    ) -> AnswerResult:
        if not retrieved_chunks:
            return AnswerResult(
                answer=SAFE_INSUFFICIENT_CONTEXT_ANSWER,
                insufficient_context=True,
                citation_chunk_ids=[],
                model_name=settings.chat_model,
                token_usage=None,
                provider=self.provider_name,
            )

        context_lines = []
        for chunk in retrieved_chunks:
            context_lines.append(
                json.dumps(
                    {
                        "chunk_id": str(chunk.chunk_id),
                        "document_title": chunk.document_title,
                        "page_number": chunk.page_number,
                        "section_title": chunk.section_title,
                        "content": chunk.content,
                    }
                )
            )

        payload = {
            "model": settings.chat_model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Question: {question}\n\nRetrieved chunks:\n"
                        + "\n".join(context_lines)
                    ),
                },
            ],
            "temperature": 0,
        }
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AnswerProviderError(f"Answer provider request failed: {exc}") from exc

        content = (
            response.json()
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        parsed = _parse_answer_json(content)
        usage = response.json().get("usage")
        return AnswerResult(
            answer=parsed["answer"],
            insufficient_context=bool(parsed["insufficient_context"]),
            citation_chunk_ids=list(parsed["citation_chunk_ids"]),
            model_name=settings.chat_model,
            token_usage=usage,
            provider=self.provider_name,
        )


def get_answer_provider() -> AnswerProvider:
    provider_name = settings.llm_provider.strip().lower()
    if provider_name == "local":
        return LocalGroundedAnswerProvider()
    if provider_name == "openai_compatible":
        return OpenAICompatibleAnswerProvider()
    raise AnswerProviderError(f"Unsupported LLM provider: {provider_name}")


def load_answer_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def _rank_chunks_for_answer(
    *,
    question: str,
    chunks: list[RetrievalResultItem],
) -> list[RetrievalResultItem]:
    terms = _question_terms(question)
    return sorted(
        chunks,
        key=lambda chunk: (
            _term_overlap_score(terms, chunk.content),
            chunk.score,
        ),
        reverse=True,
    )


def _best_snippet_for_question(question: str, content: str) -> str:
    terms = _question_terms(question)
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", content.replace("\n", " "))
        if sentence.strip()
    ]
    if not sentences:
        return content.strip()
    return max(
        sentences,
        key=lambda sentence: _term_overlap_score(terms, sentence),
    )


def _question_terms(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(term) > 2}


def _term_overlap_score(terms: set[str], text: str) -> tuple[int, int]:
    text_terms = set(re.findall(r"[a-zA-Z0-9]+", text.lower()))
    overlap = terms.intersection(text_terms)
    return (len(overlap), len(text))


def _parse_answer_json(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AnswerProviderError("Answer provider did not return valid JSON.") from exc

    answer = str(parsed.get("answer", "")).strip()
    insufficient_context = bool(parsed.get("insufficient_context", False))
    citation_chunk_ids = parsed.get("citation_chunk_ids", [])
    if not isinstance(citation_chunk_ids, list):
        raise AnswerProviderError("citation_chunk_ids must be a list.")
    if not answer:
        answer = SAFE_INSUFFICIENT_CONTEXT_ANSWER
        insufficient_context = True
        citation_chunk_ids = []
    return {
        "answer": answer,
        "insufficient_context": insufficient_context,
        "citation_chunk_ids": [str(value) for value in citation_chunk_ids],
    }
