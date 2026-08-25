"""
LLM provider abstraction.

The rest of the application depends only on this interface, never on a
specific vendor SDK. This allows swapping Gemini for OpenAI, OpenRouter,
or a local model without touching business logic (retrieval, prompts,
controllers).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

TSchema = TypeVar("TSchema", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract interface every LLM backend must implement."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a free-form text completion for the given prompt."""
        raise NotImplementedError

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: type[TSchema]) -> TSchema:
        """
        Generate a completion constrained to the given Pydantic schema and
        return a validated instance of it. Implementations should instruct
        the underlying model to return JSON only, then parse + validate,
        raising on failure rather than silently returning malformed data.
        """
        raise NotImplementedError
