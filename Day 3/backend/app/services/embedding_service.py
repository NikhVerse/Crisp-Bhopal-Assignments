import logging
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

# Global cache for the embeddings model to prevent reloading
_embeddings_instance = None

def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Initializes and returns the HuggingFace embeddings model.
    Caches the instance to avoid reloading the model on subsequent calls.
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        logger.info("Initializing HuggingFaceEmbeddings with model: sentence-transformers/all-MiniLM-L6-v2")
        try:
            _embeddings_instance = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            logger.info("HuggingFaceEmbeddings initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFaceEmbeddings: {str(e)}", exc_info=True)
            raise e
    return _embeddings_instance
