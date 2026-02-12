from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import sqlite3
import uuid
from datetime import datetime
import tempfile

# Initialize FastAPI app
app = FastAPI()

# --- CORS Configuration ---
origins = [
    "http://localhost",
    "http://localhost:5000",
    "http://localhost:5001",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5001",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount Static Files ---
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Import and Load Environment Variables ---
from dotenv import load_dotenv
load_dotenv()

# --- Try to import RAG components (graceful fallback if unavailable) ---
RAG_ENABLED = False
get_rag_chain = None
index_document_to_chroma = None
delete_doc_from_chroma = None
vectorstore = None

def lazy_load_rag():
    """Load RAG components on first use to avoid blocking server startup"""
    global RAG_ENABLED, get_rag_chain, index_document_to_chroma, delete_doc_from_chroma, vectorstore
    if RAG_ENABLED or get_rag_chain is not None:
        return  # Already loaded
    
    try:
        print("Loading RAG features...")
        from langchain_utils import get_rag_chain as _get_rag_chain
        from chroma_utils import index_document_to_chroma as _index_doc, delete_doc_from_chroma as _delete_doc, vectorstore as _vectorstore
        get_rag_chain = _get_rag_chain
        index_document_to_chroma = _index_doc
        delete_doc_from_chroma = _delete_doc
        vectorstore = _vectorstore
        RAG_ENABLED = True
        print("✓ RAG features loaded successfully")
    except ImportError as ie:
        print(f"⚠ ImportError loading RAG: {ie}")
        RAG_ENABLED = False
    except Exception as e:
        print(f"⚠ Error loading RAG: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        RAG_ENABLED = False

# --- Database Setup (SQLite) ---
DB_PATH = "app_data.db"

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS application_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_query TEXT,
            gpt_response TEXT,
            model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# --- Pydantic Models ---
class QueryInput(BaseModel):
    question: str
    session_id: Optional[str] = None
    model: str = "gemini-2.5-flash"

class QueryResponse(BaseModel):
    answer: str
    session_id: str

class DocumentInfo(BaseModel):
    id: int
    filename: str
    upload_timestamp: str

class DeleteFileRequest(BaseModel):
    file_id: int

# --- Helper Functions ---
def insert_application_logs(session_id: str, user_query: str, gpt_response: str, model: str):
    """Log chat interaction to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO application_logs (session_id, user_query, gpt_response, model) VALUES (?, ?, ?, ?)',
        (session_id, user_query, gpt_response, model)
    )
    conn.commit()
    conn.close()

def insert_document_record(filename: str) -> int:
    """Record uploaded document in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO document_store (filename) VALUES (?)', (filename,))
    conn.commit()
    file_id = cursor.lastrowid
    conn.close()
    return file_id

def delete_document_record(file_id: int):
    """Remove document record from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM document_store WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()

def get_all_documents() -> List[DocumentInfo]:
    """Fetch all uploaded documents"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, upload_timestamp FROM document_store ORDER BY upload_timestamp DESC')
    documents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return documents

# --- API Endpoints ---

@app.get("/")
async def serve_landing_page():
    """Serves the main landing page."""
    return FileResponse("static/landing.html")

@app.get("/app")
async def serve_chat_app():
    """Serves the chat application page."""
    return FileResponse("static/index.html")

@app.post("/chat")
def chat(query: QueryInput):
    """Chat endpoint with RAG capability"""
    try:
        # Generate session ID if not provided
        session_id = query.session_id or str(uuid.uuid4())
        
        print(f"[CHAT] Received query: {query.question}")
        
        # Load RAG on first use
        lazy_load_rag()
        print(f"[CHAT] RAG_ENABLED={RAG_ENABLED}")
        
        if RAG_ENABLED:
            try:
                # Get RAG chain with specified model
                print(f"[CHAT] Getting RAG chain with model: {query.model}")
                rag_chain = get_rag_chain(model=query.model)
                
                # Invoke RAG chain
                print(f"[CHAT] Invoking RAG chain...")
                result = rag_chain.invoke(query.question)
                answer = result.get("answer", "No answer generated")
                print(f"[CHAT] RAG chain invoked successfully")
            except Exception as e:
                print(f"[CHAT] Error in RAG chain: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                raise
        else:
            # Fallback: return a message indicating RAG is not enabled
            print(f"[CHAT] RAG not enabled, returning fallback message")
            answer = f"[RAG Mode Disabled] Question: {query.question}\n\nTo enable full RAG features, install: pip install langchain-community langchain-chroma python-docx pypdf"
        
        # Log interaction
        insert_application_logs(session_id, query.question, answer, query.model)
        print(f"[CHAT] Response logged successfully")
        
        return QueryResponse(answer=answer, session_id=session_id)
    
    except Exception as e:
        print(f"[CHAT] Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/upload-doc")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document"""
    try:
        print(f"[UPLOAD] Received upload request for file: {file.filename}")
        
        # Load RAG on first use
        lazy_load_rag()
        print(f"[UPLOAD] RAG_ENABLED={RAG_ENABLED}")
        
        if not RAG_ENABLED:
            raise HTTPException(
                status_code=503, 
                detail="Document upload is not available. RAG features not initialized."
            )
        
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file extension
        allowed_extensions = {'.pdf', '.docx', '.html', '.txt'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Create upload directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)
        
        # Save uploaded file
        file_path = f"uploads/{file.filename}"
        try:
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
            print(f"[UPLOAD] File saved to {file_path}")
        except Exception as e:
            print(f"[UPLOAD] Error saving file: {e}")
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
        
        # Record in database
        try:
            file_id = insert_document_record(file.filename)
            print(f"[UPLOAD] Document recorded with id: {file_id}")
        except Exception as e:
            print(f"[UPLOAD] Error recording in database: {e}")
            raise HTTPException(status_code=500, detail=f"Error recording file in database: {str(e)}")
        
        # Index document to Chroma
        try:
            print(f"[UPLOAD] Starting to index document to Chroma...")
            success = index_document_to_chroma(file_path, file_id)
            print(f"[UPLOAD] Indexing result: {success}")
        except Exception as e:
            print(f"[UPLOAD] Error indexing document: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            # Clean up if indexing fails
            delete_document_record(file_id)
            raise HTTPException(status_code=500, detail=f"Error indexing document: {str(e)}")
        
        if success:
            print(f"[UPLOAD] Successfully uploaded and indexed document")
            return {
                "message": "Document uploaded and indexed successfully",
                "file_id": file_id,
                "filename": file.filename
            }
        else:
            delete_document_record(file_id)
            raise HTTPException(status_code=400, detail="Failed to index document")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[UPLOAD] Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error uploading document: {str(e)}")

@app.get("/list-docs")
def list_documents():
    """List all uploaded documents"""
    try:
        documents = get_all_documents()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
    """Delete a document from the knowledge base"""
    try:
        # Load RAG on first use
        lazy_load_rag()
        
        if not RAG_ENABLED:
            raise HTTPException(
                status_code=503, 
                detail="Document deletion is not available. RAG features not initialized."
            )
        
        # Delete from vector store
        success = delete_doc_from_chroma(request.file_id)
        
        # Delete from database
        if success:
            delete_document_record(request.file_id)
            return {"message": "Document deleted successfully", "file_id": request.file_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete document from vector store")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "OK", "rag_enabled": RAG_ENABLED}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5001)
