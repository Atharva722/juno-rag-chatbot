from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from typing import List
from langchain_core.documents import Document
import os
from dotenv import load_dotenv

load_dotenv()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)

embedding_function = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# --- KEY CHANGE FOR RENDER FREE TIER ---
# By removing `persist_directory`, ChromaDB will run in-memory.
# This means the vector index will be lost when the app restarts or sleeps.
# This is a necessary trade-off for the free tier.
vectorstore = Chroma(embedding_function=embedding_function)

def load_and_split_document(file_path: str) -> List[Document]:
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith('.html'):
        loader = UnstructuredHTMLLoader(file_path)
    elif file_path.endswith('.txt'):
        # For text files, read directly and create documents
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        chunks = text_splitter.split_text(text)
        # Convert text chunks to Document objects
        docs = [Document(page_content=chunk, metadata={"source": file_path}) for chunk in chunks]
        return docs
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    documents = loader.load()
    return text_splitter.split_documents(documents)

def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    try:
        splits = load_and_split_document(file_path)
        for split in splits:
            split.metadata['file_id'] = file_id

        vectorstore.add_documents(splits)
        return True
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False

def delete_doc_from_chroma(file_id: int):
    # This will delete from the current in-memory collection
    try:
        # Note: This is not the most efficient way for in-memory, but it works.
        # A more advanced approach would be to get document IDs and use vectorstore.delete(ids=...)
        vectorstore._collection.delete(where={"file_id": file_id})
        print(f"Deleted all documents with file_id {file_id} from in-memory store.")
        return True
    except Exception as e:
        print(f"Error deleting document with file_id {file_id} from Chroma: {str(e)}")
        return False