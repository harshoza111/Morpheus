"""
LLM provider factory.

Returns the configured LLM provider instance, or None if no
API key is configured (graceful degradation).

To add a new provider:
  1. Create a new class implementing LLMProvider in this package.
  2. Add a branch to get_llm_provider().
  3. (Optional) Add a LLM_PROVIDER setting to config/settings.py.
"""

import logging
from functools import lru_cache

from app.services.llm.llm_base import LLMProvider

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider | None:
    """
    Return the configured LLM provider singleton.

    Supports either Gemini or OpenRouter based on LLM_PROVIDER settings.
    """
    from app.config import get_settings

    settings = get_settings()

    provider_name = (settings.LLM_PROVIDER or "").lower().strip()

    if provider_name == "openrouter":
        if not settings.OPENROUTER_API_KEY:
            logger.warning("LLM_PROVIDER is openrouter but OPENROUTER_API_KEY is not set.")
            return None
        from app.services.llm.openrouter_provider import OpenRouterProvider
        logger.info("LLM provider: OpenRouter (%s)", settings.OPENROUTER_MODEL)
        return OpenRouterProvider(api_key=settings.OPENROUTER_API_KEY, model=settings.OPENROUTER_MODEL)
    
    elif provider_name == "gemini":
        if not settings.GEMINI_API_KEY:
            logger.warning("LLM_PROVIDER is gemini but GEMINI_API_KEY is not set.")
            return None
        from app.services.llm.gemini_provider import GeminiProvider
        logger.info("LLM provider: Gemini (gemini-2.0-flash)")
        return GeminiProvider(api_key=settings.GEMINI_API_KEY)

    # Graceful degradation / auto-detection fallback
    if settings.OPENROUTER_API_KEY:
        from app.services.llm.openrouter_provider import OpenRouterProvider
        logger.info("LLM provider auto-detected: OpenRouter (%s)", settings.OPENROUTER_MODEL)
        return OpenRouterProvider(api_key=settings.OPENROUTER_API_KEY, model=settings.OPENROUTER_MODEL)
    elif settings.GEMINI_API_KEY:
        from app.services.llm.gemini_provider import GeminiProvider
        logger.info("LLM provider auto-detected: Gemini (gemini-2.0-flash)")
        return GeminiProvider(api_key=settings.GEMINI_API_KEY)

    logger.warning("No LLM provider keys configured — AI summaries and logs auto-classification disabled")
    return None
