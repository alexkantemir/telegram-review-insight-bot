from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class KnowledgeSnippet:
    source: str
    content: str
    score: float = 1.0


class KnowledgeProvider(ABC):
    @abstractmethod
    async def get_context(self, query: str, limit: int = 3) -> list[KnowledgeSnippet]:
        """Return relevant knowledge snippets for the given query."""


class LocalKnowledgeProvider(KnowledgeProvider):
    """Simple keyword-based local knowledge lookup without a vector database."""

    def __init__(self, entries: list[dict[str, str]] | None = None) -> None:
        self._entries = entries or [
            {
                "source": "policy_returns",
                "content": "Возврат принимается в течение 30 дней при сохранении оригинальной упаковки.",
                "keywords": "return refund exchange возврат обмен refund",
            },
            {
                "source": "policy_delivery",
                "content": "Стандартная доставка занимает 3–5 рабочих дней; экспресс — 1–2 дня.",
                "keywords": "delivery shipping late package доставка посылка опоздание",
            },
            {
                "source": "policy_support",
                "content": "Поддержка отвечает в течение 24 часов в рабочие дни.",
                "keywords": "support contact manager help поддержка менеджер связь",
            },
        ]

    async def get_context(self, query: str, limit: int = 3) -> list[KnowledgeSnippet]:
        query_lower = query.lower()
        scored: list[tuple[float, KnowledgeSnippet]] = []

        for entry in self._entries:
            keywords = entry.get("keywords", "").split()
            matches = sum(1 for keyword in keywords if keyword in query_lower)
            if matches == 0:
                continue
            score = matches / max(len(keywords), 1)
            scored.append(
                (
                    score,
                    KnowledgeSnippet(
                        source=entry["source"],
                        content=entry["content"],
                        score=score,
                    ),
                )
            )

        scored.sort(key=lambda item: item[0], reverse=True)
        return [snippet for _, snippet in scored[:limit]]


class VectorKnowledgeProvider(KnowledgeProvider):
    """
    Placeholder adapter for future vector search integration (e.g. ChromaDB, Pinecone).
    Not required for MVP — returns empty context until implemented.
    """

    def __init__(self, collection_name: str = "reviews_knowledge") -> None:
        self.collection_name = collection_name

    async def get_context(self, query: str, limit: int = 3) -> list[KnowledgeSnippet]:
        # Future: connect to vector DB and perform semantic search.
        return []


def format_knowledge_context(snippets: list[KnowledgeSnippet]) -> str:
    if not snippets:
        return "Дополнительный контекст знаний недоступен."
    lines = [f"- [{snippet.source}] {snippet.content}" for snippet in snippets]
    return "\n".join(lines)
