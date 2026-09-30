import logging
from langchain_openai import ChatOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_llm() -> ChatOpenAI:
    """
    Initializes and returns a ChatOpenAI model configured to use the Grok API
    or another OpenAI-compatible base URL.
    """
    logger.info(f"Initializing ChatOpenAI model: {settings.MODEL_NAME} (Base URL: {settings.GROK_BASE_URL})")
    try:
        # Validate that we have an API key configured
        if not settings.GROK_API_KEY or settings.GROK_API_KEY == "your_grok_api_key_here":
            logger.warning("GROK_API_KEY is not set or has the placeholder value. Please check your .env file.")
            
        llm = ChatOpenAI(
            api_key=settings.GROK_API_KEY,
            base_url=settings.GROK_BASE_URL,
            model=settings.MODEL_NAME,
            temperature=0.0,  # 0.0 temperature ensures factual answers and minimizes hallucinations
        )
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {str(e)}", exc_info=True)
        raise e
