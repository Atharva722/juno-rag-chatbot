from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from langchain_utils import get_rag_chain
from db_utils import (
    insert_application_logs, get_chat_history, get_all_documents, 
    insert_document_record, delete_document_record
)
from chroma_utils import index_document_to_chroma, delete_doc_from_chroma
import os
import uuid
import logging
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastAPI app
app = FastAPI()

# --- CORS Configuration ---
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
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
# This makes the 'static' folder available to the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- API Endpoints (Backend Logic) ---

@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    session_id = query_input.session_id if query_input.session_id else str(uuid.uuid4())
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model.value}")

    chat_history = get_chat_history(session_id)
    
    # Use Gemini model
    rag_chain = get_rag_chain(query_input.model.value)
    
    try:
        answer = rag_chain.invoke({
            "input": query_input.question,
            "chat_history": chat_history
        })['answer']
        insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
        logging.info(f"Session ID: {session_id}, AI Response: {answer}")
        return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)
    except Exception as e:
        logging.error(f"Error during RAG chain invocation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-doc")
def upload_and_index_document(file: UploadFile = File(...)):
    allowed_extensions = ['.pdf', '.docx', '.html', '.txt', '.csv']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")

    temp_file_path = f"temp_{file.filename}"

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_id = insert_document_record(file.filename)
        success = index_document_to_chroma(temp_file_path, file_id)

        if success:
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            delete_document_record(file_id) # Rollback DB entry
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}.")
    except Exception as e:
        logging.error(f"Error during file upload: {e}")
        # Ensure file_id is defined before trying to delete
        if 'file_id' in locals():
            delete_document_record(file_id)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/list-docs", response_model=list[DocumentInfo])
def list_documents():
    return get_all_documents()

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
    chroma_delete_success = delete_doc_from_chroma(request.file_id)

    if chroma_delete_success:
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {request.file_id}."}
        else:
             raise HTTPException(status_code=500, detail="Deleted from vector store but failed to delete from database.")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete document from vector store.")


# --- Frontend Serving ---

@app.get("/", response_class=HTMLResponse)
async def serve_landing_page():
    """Serves the main landing page."""
    return FileResponse("static/landing.html")

@app.get("/app", response_class=HTMLResponse)
async def serve_chat_app():
    """Serves the chat application page."""
    return FileResponse("static/index.html")