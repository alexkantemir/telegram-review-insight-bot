import json
import re
from typing import Any

from openai import AsyncOpenAI

from bot.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIService:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def chat_json(
        self,
        system_prompt: str,
        user_message: str,
        max_retries: int = 2,
    ) -> dict[str, Any]:
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )
                content = response.choices[0].message.content
                if not content:
                    raise ValueError("Empty response from OpenAI")
                return self._parse_json_content(content)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "OpenAI JSON request failed (attempt %s/%s): %s",
                    attempt + 1,
                    max_retries + 1,
                    exc,
                )

        assert last_error is not None
        raise last_error

    @staticmethod
    def _parse_json_content(content: str) -> dict[str, Any]:
        cleaned = content.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            extracted = OpenAIService._extract_json_object(cleaned)
            if extracted is None:
                raise ValueError(f"Invalid JSON from model: {exc}") from exc
            parsed = json.loads(extracted)

        if not isinstance(parsed, dict):
            raise ValueError("Model response is not a JSON object")
        return parsed

    @staticmethod
    def _extract_json_object(text: str) -> str | None:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return text[start : end + 1]
