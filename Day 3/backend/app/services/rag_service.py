import logging
from typing import List, Dict
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.services.chroma_service import get_vectorstore
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)

def query_rag(question: str, history: List[Dict[str, str]]) -> str:
    """
    Retrieves context for the question, constructs the prompt using history,
    sends it to the LLM, and returns the response.
    
    Args:
        question (str): The current query from the user.
        history (List[Dict[str, str]]): List of previous messages in the format
                                        [{"role": "user"|"assistant", "content": "text"}].
                                        
    Returns:
        str: The AI response.
    """
    try:
        # 1. Get vector store
        db = get_vectorstore()
        if db is None:
            raise ValueError("No PDF has been uploaded yet. Please upload a PDF first.")
            
        # 2. Retrieve relevant chunks from Chroma
        logger.info(f"Retrieving relevant chunks for query: '{question}'")
        # Retrieve the top 5 chunks for better coverage
        docs = db.similarity_search(question, k=5)
        
        # Combine chunks content
        context_list = [doc.page_content for doc in docs]
        context = "\n\n---\n\n".join(context_list)
        logger.info(f"Retrieved {len(docs)} relevant chunks from Chroma.")
        
        # 3. Get LLM Instance
        llm = get_llm()
        
        # 4. Construct messages with strict instructions and context
        system_content = (
            "You are an AI assistant.\n\n"
            "Answer ONLY from the supplied context.\n"
            "If the answer is unavailable, reply:\n"
            "'I couldn't find that information in the uploaded PDF.'\n"
            "Keep answers accurate.\n"
            "Use bullet points whenever appropriate.\n\n"
            f"Supplied Context:\n{context}"
        )
        
        messages = [SystemMessage(content=system_content)]
        
        # Append conversation history
        for msg in history:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
                
        # Append the final query
        messages.append(HumanMessage(content=question))
        
        # 5. Call LLM
        logger.info("Sending messages chain to LLM (Grok)...")
        response = llm.invoke(messages)
        
        logger.info("Received response from LLM.")
        return str(response.content)
        
    except Exception as e:
        logger.error(f"Error in RAG query process: {str(e)}", exc_info=True)
        raise e
