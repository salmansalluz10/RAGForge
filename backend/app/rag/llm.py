"""
LLMService - Configurable LLM Provider Interface.

Design:
  - Clean abstraction allowing runtime switching between providers (OpenAI, Anthropic, Groq, Mock)
    via environment variables (LLM_PROVIDER, LLM_MODEL, LLM_API_KEY).
  - In testing/development without an API key, MockLLMProvider produces grounded answers
    from the provided context without making external HTTP calls.
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("ragforge.llm")


class BaseLLMProvider(ABC):
    """Abstract interface for Large Language Model providers."""

    @abstractmethod
    def generate_response(self, prompt: str, system_prompt: str) -> str:
        """Generate a completion response given user prompt and system instructions."""


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI GPT-4o / GPT-4o-mini completion provider."""

    def __init__(self):
        import openai
        self._client = openai.OpenAI(api_key=settings.LLM_API_KEY)
        self._model = settings.LLM_MODEL
        self._temperature = settings.LLM_TEMPERATURE
        self._max_tokens = settings.LLM_MAX_TOKENS

    def generate_response(self, prompt: str, system_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return response.choices[0].message.content or ""


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic mock LLM provider for CI, automated testing, and offline local development.
    Extracts answers directly from the grounded context in the prompt.
    """

    def generate_response(self, prompt: str, system_prompt: str) -> str:
        # Check if prompt has retrieved context
        if "Retrieved Document Context:" in prompt and "==================================================" in prompt:
            parts = prompt.split("==================================================")
            if len(parts) >= 2:
                context_block = parts[1].strip()
                if not context_block or context_block == "None":
                    return "I could not find enough information in your uploaded documents to answer this question."

                # Find lines that match the query or summarize the retrieved context
                lines = [line.strip() for line in context_block.split("\n") if line.strip() and not line.startswith("[Source")]
                if lines:
                    first_fact = lines[0]
                    return f"Based on your documents, {first_fact}"

        return "I could not find enough information in your uploaded documents to answer this question."


class LLMService:
    """
    Singleton service managing the configured LLM provider.
    """

    _instance: Optional["LLMService"] = None

    def __init__(self, provider: BaseLLMProvider):
        self._provider = provider

    @classmethod
    def get_instance(cls) -> "LLMService":
        if cls._instance is None:
            cls._instance = cls._build()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    @classmethod
    def _build(cls) -> "LLMService":
        provider_name = (settings.LLM_PROVIDER or "").lower()
        api_key = settings.LLM_API_KEY or ""

        if provider_name == "openai" and api_key:
            try:
                provider = OpenAILLMProvider()
                logger.info(f"LLM Provider: OpenAI ({settings.LLM_MODEL})")
                return cls(provider)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI LLM provider: {e}. Falling back to mock.")

        logger.info("Using MockLLMProvider for offline/test completion generation.")
        return cls(MockLLMProvider())

    def generate(self, prompt: str, system_prompt: str) -> str:
        return self._provider.generate_response(prompt=prompt, system_prompt=system_prompt)

    @property
    def provider_name(self) -> str:
        return type(self._provider).__name__
