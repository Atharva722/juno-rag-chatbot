from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from chroma_utils import vectorstore
from dotenv import load_dotenv
import os

load_dotenv()

def get_rag_chain(model="gemini-2.5-flash"):
    """
    Get RAG chain with Google Gemini LLM.
    
    Args:
        model: Gemini model name (e.g., "gemini-2.5-flash", "gemini-pro")
    """
    
    llm = ChatGoogleGenerativeAI(
        model=model,
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    
    # Create a simple RAG prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI assistant. Use the provided context to answer questions."),
        ("system", "Context:\n{context}"),
        ("human", "{input}"),
    ])
    
    # Helper function to format documents
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    # Build the RAG chain manually
    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "input": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # Wrapper to return dict with 'answer' key for compatibility
    class RAGChainWrapper:
        def __init__(self, chain):
            self.chain = chain
        
        def invoke(self, input_text):
            """Invoke the RAG chain with a text input"""
            result = self.chain.invoke(input_text)
            return {"answer": result}
    
    return RAGChainWrapper(rag_chain)
