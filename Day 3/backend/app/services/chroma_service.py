import os
import shutil
import logging
from typing import List, Optional
from langchain_core.documents import Document
from langchain_chroma import Chroma
from app.core.config import settings
from app.services.embedding_service import get_embeddings

logger = logging.getLogger(__name__)

# Global cache for the vector store instance
_vectorstore_instance: Optional[Chroma] = None

def get_vectorstore() -> Optional[Chroma]:
    """
    Retrieves the current Chroma vectorstore instance if it exists.
    If database files exist but the instance is not loaded, it loads it.
    """
    global _vectorstore_instance
    if _vectorstore_instance is not None:
        return _vectorstore_instance
        
    db_dir = settings.VECTORSTORE_DIR
    # Check if the database folder has been created/populated
    if os.path.exists(db_dir) and len(os.listdir(db_dir)) > 0:
        logger.info(f"Loading existing Chroma vectorstore from: {db_dir}")
        try:
            embeddings = get_embeddings()
            _vectorstore_instance = Chroma(
                persist_directory=db_dir,
                embedding_function=embeddings
            )
            return _vectorstore_instance
        except Exception as e:
            logger.error(f"Error loading existing Chroma vectorstore: {str(e)}", exc_info=True)
            return None
    return None

def create_vectorstore(documents: List[Document]) -> Chroma:
    """
    Clears any existing vectorstore and creates a new one with the provided documents.
    """
    global _vectorstore_instance
    try:
        # Clear database directory first to ensure clean state
        clear_vectorstore()
        
        db_dir = settings.VECTORSTORE_DIR
        logger.info(f"Creating new Chroma vectorstore at: {db_dir} with {len(documents)} documents.")
        
        embeddings = get_embeddings()
        _vectorstore_instance = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=db_dir
        )
        logger.info("Chroma vectorstore successfully created.")
        return _vectorstore_instance
    except Exception as e:
        logger.error(f"Error creating Chroma vectorstore: {str(e)}", exc_info=True)
        raise e

def clear_vectorstore() -> None:
    """
    Completely deletes the Chroma database directory, resets global references, and cleans upload dir.
    """
    global _vectorstore_instance
    logger.info("Clearing Chroma vectorstore and upload directories.")
    
    # 1. Reset database instance reference
    _vectorstore_instance = None
    
    # 2. Delete the database directory
    db_dir = settings.VECTORSTORE_DIR
    if os.path.exists(db_dir):
        try:
            shutil.rmtree(db_dir)
            logger.info("Successfully deleted vectorstore directory.")
        except Exception as e:
            logger.warning(f"Could not fully delete vectorstore directory: {str(e)}. Attempting to clear contents.")
            for root, dirs, files in os.walk(db_dir, topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                    except Exception:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except Exception:
                        pass
                        
    # Re-create the empty directory
    os.makedirs(db_dir, exist_ok=True)
    
    # 3. Clean uploads directory to keep only the latest PDF
    upload_dir = settings.UPLOAD_DIR
    if os.path.exists(upload_dir):
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.warning(f"Failed to delete uploaded file {file_path}: {str(e)}")
