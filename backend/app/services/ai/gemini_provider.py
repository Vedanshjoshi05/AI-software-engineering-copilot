"""
Gemini implementation of LLMProvider.

Uses the Gemini REST API directly via httpx.

Features:
- Gemini 3.x compatible generation
- Configurable model fallback
- Retry handling for 429/503
- Structured JSON generation
- Pydantic schema validation
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.logging import logger
from app.services.ai.llm_provider import LLMProvider


TSchema = TypeVar("TSchema", bound=BaseModel)

GEMINI_BASE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
)


class LLMGenerationError(Exception):
    """Raised when every configured model/retry attempt has failed."""


class GeminiProvider(LLMProvider):
    def __init__(
        self,
        api_key: str | None = None,
        models: list[str] | None = None,
        max_retries: int = 2,
        http_client: httpx.AsyncClient | None = None,
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.models = models or settings.generation_models_list
        self.max_retries = max_retries
        self._client = http_client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=60.0,
            )

        return self._client

    async def generate(
        self,
        prompt: str,
        generation_config: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a free-form response using Gemini.

        generation_config is optional and is used by structured
        generation to request JSON output.
        """
        client = await self._get_client()

        if not self.api_key:
            raise LLMGenerationError(
                "Gemini API key is not configured."
            )

        if not self.models:
            raise LLMGenerationError(
                "No Gemini generation models are configured."
            )

        last_error: Exception | None = None

        for model in self.models:
            model = model.strip()

            if not model:
                continue

            logger.info(
                "Trying Gemini model: %s",
                model,
            )

            for attempt in range(self.max_retries + 1):
                try:
                    request_body: dict[str, Any] = {
                        "contents": [
                            {
                                "parts": [
                                    {
                                        "text": prompt,
                                    }
                                ]
                            }
                        ]
                    }

                    if generation_config is not None:
                        request_body["generationConfig"] = (
                            generation_config
                        )

                    response = await client.post(
                        f"{GEMINI_BASE_URL}/{model}:generateContent",
                        headers={
                            "x-goog-api-key": self.api_key,
                            "Content-Type": "application/json",
                        },
                        json=request_body,
                    )

                    response.raise_for_status()

                    data = response.json()

                    text = self._extract_text(data)

                    if not text.strip():
                        raise ValueError(
                            "Gemini returned an empty response."
                        )

                    logger.info(
                        "Answer generated using: %s",
                        model,
                    )

                    return text

                except httpx.HTTPStatusError as error:
                    last_error = error
                    status_code = error.response.status_code

                    retryable = status_code in (
                        429,
                        503,
                    )

                    if not retryable:
                        try:
                            error_body = error.response.json()
                        except ValueError:
                            error_body = error.response.text

                        logger.warning(
                            "%s failed with status %s: %s",
                            model,
                            status_code,
                            error_body,
                        )

                        break

                    if attempt == self.max_retries:
                        logger.warning(
                            "%s still unavailable after %d attempts. "
                            "Trying fallback model...",
                            model,
                            self.max_retries + 1,
                        )

                        break

                    delay = 2 * (2**attempt)

                    logger.warning(
                        "%s unavailable (%s). "
                        "Retrying in %ds...",
                        model,
                        status_code,
                        delay,
                    )

                    await asyncio.sleep(delay)

                except (
                    httpx.RequestError,
                    ValueError,
                ) as error:
                    last_error = error

                    logger.warning(
                        "%s request failed: %s. "
                        "Trying fallback model...",
                        model,
                        error,
                    )

                    break

        logger.error(
            "All Gemini generation models failed"
        )

        raise LLMGenerationError(
            str(last_error)
            if last_error
            else "LLM generation failed"
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: type[TSchema],
    ) -> TSchema:
        """
        Generate structured JSON using Gemini.

        Gemini is explicitly instructed to return JSON through
        responseMimeType.

        The Pydantic JSON schema is included in the prompt for
        guidance, but is NOT sent as responseSchema because Pydantic
        schemas can contain $defs/$ref fields that Gemini's REST
        responseSchema does not accept.

        The final response is parsed and validated locally using
        Pydantic.
        """
        schema_json = schema.model_json_schema()

        structured_prompt = f"""
{prompt}

IMPORTANT:

Return ONLY one valid JSON object.

Do not use markdown code fences.
Do not include a preamble.
Do not include explanations outside the JSON.

The JSON object MUST conform to this schema:

{json.dumps(schema_json, indent=2)}
"""

        raw_text = await self.generate(
            structured_prompt,
            generation_config={
                "responseMimeType": "application/json",
            },
        )

        return self._parse_structured(
            raw_text,
            schema,
        )

    @staticmethod
    def _extract_text(
        data: dict[str, Any],
    ) -> str:
        """
        Extract text from a Gemini generateContent response.
        """
        try:
            candidates = data["candidates"]

            if not candidates:
                raise ValueError(
                    "Gemini returned no candidates."
                )

            content = candidates[0]["content"]
            parts = content["parts"]

            return "".join(
                part.get("text", "")
                for part in parts
                if isinstance(part, dict)
            )

        except (
            KeyError,
            IndexError,
            TypeError,
        ) as error:
            raise ValueError(
                "Unexpected Gemini response shape: "
                f"{data}"
            ) from error

    @staticmethod
    def _parse_structured(
        raw_text: str,
        schema: type[TSchema],
    ) -> TSchema:
        """
        Parse Gemini JSON and validate it against the
        requested Pydantic schema.
        """
        candidate = raw_text.strip()

        # Remove markdown code fences if Gemini returns them.
        fence_match = re.search(
            r"```(?:json)?\s*([\s\S]*?)```",
            candidate,
            flags=re.IGNORECASE,
        )

        if fence_match:
            candidate = fence_match.group(1).strip()

        try:
            payload = json.loads(candidate)

        except json.JSONDecodeError as error:
            # Fallback: find the first JSON object.
            brace_match = re.search(
                r"\{[\s\S]*\}",
                candidate,
            )

            if not brace_match:
                raise LLMGenerationError(
                    "Model did not return valid JSON: "
                    f"{error}"
                ) from error

            try:
                payload = json.loads(
                    brace_match.group(0)
                )

            except json.JSONDecodeError as nested_error:
                raise LLMGenerationError(
                    "Model returned malformed JSON."
                ) from nested_error

        try:
            return schema.model_validate(
                payload
            )

        except ValidationError as error:
            raise LLMGenerationError(
                "Model JSON did not match expected schema: "
                f"{error}"
            ) from error