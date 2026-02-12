# pydantic_models.py

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
# Remove this line if you are on Python 3.9 or older
from typing import Optional 

class ModelName(str, Enum):
    LLAMA3_1_8B = "llama-3.1-8b-instant"
    # FIX: Use the new, supported model name
    MIXTRAL_8X7B = "mixtral-8x7b-groq" 


class QueryInput(BaseModel):
    question: str
    # FIX: Make session_id explicitly optional to handle 'null' from the frontend
    session_id: Optional[str] = Field(default=None) 
    model: ModelName = Field(default=ModelName.LLAMA3_1_8B)

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    model: ModelName

class DocumentInfo(BaseModel):
    id: int
    filename: str
    upload_timestamp: datetime

class DeleteFileRequest(BaseModel):
    file_id: int