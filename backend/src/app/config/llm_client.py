import logging
from functools import lru_cache
from typing import Any
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@lru_cache()
def get_llm():
    """
    Return a LangChain ChatGroq instance if GROQ_API_KEY is configured,
    or a LangChain Google GenAI client / fallback.
    """
    if settings.groq_api_key:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                api_key=settings.groq_api_key,
                model=settings.llm_model,
                temperature=0.3,
                max_tokens=800,
            )
        except Exception as e:
            logger.warning(f"Could not initialize ChatGroq: {e}")
    
    # Fallback to langchain_google_genai if available
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        if settings.gemini_api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=settings.gemini_api_key,
                temperature=0.3,
            )
    except Exception:
        pass

    # Default Groq client
    from langchain_groq import ChatGroq
    return ChatGroq(
        api_key=settings.groq_api_key or "dummy_groq_key",
        model=settings.llm_model,
        temperature=0.3,
        max_tokens=800,
    )
