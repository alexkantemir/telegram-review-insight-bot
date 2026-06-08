import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from bot.schemas.review_analysis import (
    ReviewAnalysis,
    ReviewType,
    Sentiment,
    Topic,
)
from bot.services.knowledge_provider import KnowledgeSnippet, KnowledgeProvider, format_knowledge_context
from bot.services.openai_service import OpenAIService
from bot.utils.logger import get_logger

logger = get_logger(__name__)

SAFE_POLICY_QUESTION_REPLY = (
    "Спасибо за ваш вопрос! Чтобы дать точный и корректный ответ, "
    "нам нужно уточнить актуальные условия компании по вашему случаю. "
    "Мы передадим запрос специалисту и вернёмся с официальной информацией "
    "в ближайшее время."
)

POLICY_TOPICS = frozenset({
    Topic.RETURN,
    Topic.DELIVERY,
    Topic.PRICE,
})

POLICY_KEYWORDS = (
    "возврат",
    "обмен",
    "гарант",
    "доставк",
    "оплат",
    "срок",
    "стоимост",
    "компенсац",
    "рубл",
    "тариф",
    "курьер",
    "обратн",
    "отправк",
)

RISKY_REPLY_TERMS = (
    "бесплатн",
    "оплачива",
    "компенсац",
    "гарант",
    "в течение",
    "рабочих дн",
)


class ReviewAnalyzer:
    def __init__(
        self,
        openai_service: OpenAIService,
        knowledge_provider: KnowledgeProvider,
        system_prompt_path: Path,
        max_retries: int = 2,
    ) -> None:
        self._openai = openai_service
        self._knowledge = knowledge_provider
        self._system_prompt_path = system_prompt_path
        self._max_retries = max_retries
        self._system_prompt_template = system_prompt_path.read_text(encoding="utf-8")

    async def analyze(self, review_text: str) -> ReviewAnalysis:
        snippets = await self._knowledge.get_context(review_text)
        knowledge_context = format_knowledge_context(snippets)
        system_prompt = self._system_prompt_template.format(
            knowledge_context=knowledge_context
        )

        last_validation_error: ValidationError | None = None
        raw_payload: dict[str, Any] | None = None

        for attempt in range(self._max_retries + 1):
            try:
                raw_payload = await self._openai.chat_json(
                    system_prompt=system_prompt,
                    user_message=f"Отзыв клиента:\n{review_text}",
                    max_retries=1,
                )
                analysis = ReviewAnalysis.model_validate(raw_payload)
                return self._apply_safe_policy_reply(analysis, snippets, review_text)
            except ValidationError as exc:
                last_validation_error = exc
                logger.warning(
                    "Review analysis validation failed (attempt %s/%s): %s",
                    attempt + 1,
                    self._max_retries + 1,
                    exc,
                )
                system_prompt = (
                    system_prompt
                    + "\n\nПредыдущий ответ был некорректным. "
                    "Верни только валидный JSON, соответствующий требуемой схеме и значениям enum."
                )
            except Exception as exc:
                logger.error("Review analysis failed: %s", exc)
                raise

        if raw_payload is not None:
            fallback = self._safe_fallback_parse(raw_payload, review_text)
            if fallback is not None:
                logger.warning("Using safe fallback parsing for invalid model response")
                return fallback

        assert last_validation_error is not None
        raise last_validation_error

    @staticmethod
    def _safe_fallback_parse(payload: dict[str, Any], review_text: str) -> ReviewAnalysis | None:
        try:
            sentiment = ReviewAnalyzer._coerce_enum(
                payload.get("sentiment"), Sentiment, Sentiment.NEUTRAL
            )
            topic = ReviewAnalyzer._coerce_enum(
                payload.get("topic"), Topic, Topic.OTHER
            )
            short_summary = str(payload.get("short_summary") or review_text[:200]).strip()
            escalation_required = bool(payload.get("escalation_required", False))
            review_type = ReviewAnalyzer._coerce_enum(
                payload.get("review_type"), ReviewType, ReviewType.QUESTION
            )
            suggested_reply = str(
                payload.get("suggested_reply")
                or (
                    SAFE_POLICY_QUESTION_REPLY
                    if review_type == ReviewType.QUESTION
                    else "Спасибо за ваш отзыв. Мы уже рассматриваем ваше обращение и скоро свяжемся с вами."
                )
            ).strip()

            return ReviewAnalysis(
                sentiment=sentiment,
                review_type=review_type,
                topic=topic,
                short_summary=short_summary[:500],
                escalation_required=escalation_required,
                suggested_reply=suggested_reply[:2000],
            )
        except Exception as exc:
            logger.error("Fallback parsing failed: %s", exc)
            return None

    def _apply_safe_policy_reply(
        self,
        analysis: ReviewAnalysis,
        snippets: list[KnowledgeSnippet],
        review_text: str,
    ) -> ReviewAnalysis:
        if not self._is_policy_question(analysis, review_text):
            return analysis

        knowledge_text = " ".join(snippet.content for snippet in snippets)
        if not snippets or self._reply_exceeds_knowledge(analysis.suggested_reply, knowledge_text):
            logger.info(
                "Применён безопасный suggested_reply для вопроса о политике без подтверждённых правил"
            )
            return analysis.model_copy(update={"suggested_reply": SAFE_POLICY_QUESTION_REPLY})
        return analysis

    @staticmethod
    def _is_policy_question(analysis: ReviewAnalysis, review_text: str) -> bool:
        if analysis.review_type != ReviewType.QUESTION:
            return False
        if analysis.topic in POLICY_TOPICS:
            return True
        text_lower = review_text.lower()
        return any(keyword in text_lower for keyword in POLICY_KEYWORDS)

    @staticmethod
    def _reply_exceeds_knowledge(reply: str, knowledge_text: str) -> bool:
        if not knowledge_text.strip():
            return True

        reply_lower = reply.lower()
        knowledge_lower = knowledge_text.lower()

        reply_numbers = set(re.findall(r"\d+", reply_lower))
        knowledge_numbers = set(re.findall(r"\d+", knowledge_lower))
        if reply_numbers - knowledge_numbers:
            return True

        return any(
            term in reply_lower and term not in knowledge_lower
            for term in RISKY_REPLY_TERMS
        )

    @staticmethod
    def _coerce_enum(value: Any, enum_cls, default):
        if value is None:
            return default
        normalized = str(value).strip().lower()
        for member in enum_cls:
            if member.value == normalized:
                return member
        return default
