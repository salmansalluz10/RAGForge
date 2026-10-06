"""
LLMService - Configurable LLM Provider Interface.

Supported Providers:
  - GeminiLLMProvider (Official google-genai SDK, gemini-2.5-flash, grounded generation)
  - OpenAILLMProvider (Official openai SDK, gpt-4o-mini / gpt-4o)
  - MockLLMProvider (Deterministic mock provider, ONLY selected when LLM_PROVIDER=mock)
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


class GeminiLLMProvider(BaseLLMProvider):
    """
    Google Gemini Large Language Model provider using the official google-genai SDK.
    Uses model: gemini-2.5-flash (or configured settings.LLM_MODEL).
    Accepts system instructions, temperature, thinking budget, and max output tokens.
    """

    def __init__(self, api_key: Optional[str] = None):
        from google import genai
        key = api_key or settings.effective_gemini_api_key
        if not key:
            raise ValueError("Gemini API key is required but not configured.")
        self._client = genai.Client(api_key=key)
        self._model = settings.LLM_MODEL
        self._temperature = settings.LLM_TEMPERATURE
        self._max_tokens = settings.LLM_MAX_TOKENS

    def generate_response(self, prompt: str, system_prompt: str) -> str:
        """Generate a grounded completion using Gemini."""
        from google.genai import types

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=self._temperature,
                max_output_tokens=self._max_tokens,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )

            # Robust extraction of generated response text
            text = response.text or ""
            if not text and getattr(response, "candidates", None):
                parts = []
                for cand in response.candidates:
                    if cand.content and cand.content.parts:
                        for part in cand.content.parts:
                            if getattr(part, "text", None):
                                parts.append(part.text)
                text = "".join(parts)

            return text.strip()
        except Exception as e:
            logger.error(f"Gemini LLM generate_response error: {e}", exc_info=True)
            raise


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI GPT-4o / GPT-4o-mini completion provider."""

    def __init__(self, api_key: Optional[str] = None):
        import openai
        key = api_key or settings.LLM_API_KEY
        if not key:
            raise ValueError("OpenAI API key is required but not configured.")
        self._client = openai.OpenAI(api_key=key)
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
    Deterministic mock LLM provider for CI and automated testing.
    Only selected when LLM_PROVIDER=mock is explicitly configured.
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
        gemini_key = settings.effective_gemini_api_key
        openai_key = settings.LLM_API_KEY or ""

        if provider_name == "gemini":
            if gemini_key:
                try:
                    provider = GeminiLLMProvider(api_key=gemini_key)
                    logger.info(f"Using GeminiLLMProvider with model {settings.LLM_MODEL}")
                    return cls(provider)
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini LLM provider: {e}", exc_info=True)
                    raise RuntimeError(f"Failed to initialize Gemini LLM provider: {e}")
            else:
                error_msg = (
                    "LLM_PROVIDER='gemini' is configured, but neither GEMINI_API_KEY nor "
                    "EMBEDDING_API_KEY is set. Real Gemini LLM generation requires a valid API key."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

        elif provider_name == "openai":
            if openai_key:
                try:
                    provider = OpenAILLMProvider(api_key=openai_key)
                    logger.info(f"Using OpenAILLMProvider with model {settings.LLM_MODEL}")
                    return cls(provider)
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI LLM provider: {e}", exc_info=True)
                    raise RuntimeError(f"Failed to initialize OpenAI LLM provider: {e}")
            else:
                error_msg = (
                    "LLM_PROVIDER='openai' is configured, but LLM_API_KEY is empty. "
                    "Real OpenAI LLM generation requires a valid API key."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

        elif provider_name == "mock":
            logger.info("Using MockLLMProvider explicitly configured for testing/offline use.")
            return cls(MockLLMProvider())

        else:
            error_msg = f"Unsupported LLM provider '{provider_name}'. Supported providers: 'gemini', 'openai', 'mock'."
            logger.error(error_msg)
            raise ValueError(error_msg)

    def generate(self, prompt: str, system_prompt: str) -> str:
        return self._provider.generate_response(prompt=prompt, system_prompt=system_prompt)

    @property
    def provider_name(self) -> str:
        return type(self._provider).__name__
