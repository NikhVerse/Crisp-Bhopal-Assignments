import logging
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def load_and_split_pdf(file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
    """
    Loads a PDF file and splits its contents into document chunks.
    
    Args:
        file_path (str): The absolute path to the PDF file.
        chunk_size (int): Max size of each text chunk. Default is 1000.
        chunk_overlap (int): Overlap between chunks. Default is 200.
        
    Returns:
        List[Document]: A list of text chunk document objects.
    """
    try:
        logger.info(f"Loading PDF from path: {file_path}")
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        if not documents:
            raise ValueError("The uploaded PDF is empty or could not be parsed.")
            
        logger.info(f"Successfully loaded PDF. Total pages: {len(documents)}")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Successfully split PDF into {len(chunks)} chunks.")
        return chunks
        
    except Exception as e:
        logger.error(f"Error loading or splitting PDF: {str(e)}", exc_info=True)
        raise e
