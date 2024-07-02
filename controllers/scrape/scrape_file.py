from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List
from fastapi import Depends, APIRouter, Query, status, Body
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from fastapi.middleware.cors import CORSMiddleware
from fastapi_versioning import VersionedFastAPI, version
import os
import base64
import tempfile
from langchain_text_splitters import CharacterTextSplitter

router = APIRouter()

os.makedirs('stored_embeds/files', exist_ok=True)

class FileRequest(BaseModel):
    name: str
    content_type: str
    content: str 

@router.post('/scrape-and-store-file', response_model=dict)
@version(1)
async def scrape_and_store(request: FileRequest):
    name = request.name
    content_type = request.content_type
    content = request.content
    
    if content_type.lower() != 'pdf':
        raise HTTPException(status_code=400, detail="Unsupported content type. Only 'pdf' is allowed.")
    
    try:
        file_data = base64.b64decode(content)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error decoding file content: {str(e)}")
    
    try:
        loader = PyPDFLoader(temp_file_path)
        pages = loader.load_and_split()
        content = "\n".join(page.page_content for page in pages)        
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)        
        docs = text_splitter.split_documents(pages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scraping PDF content: {str(e)}")
    finally:
        os.remove(temp_file_path) 
    
    try:
        embeddings = OpenAIEmbeddings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")
    
    try:        
        db = FAISS.from_documents(docs, embeddings)
        name_without_extension = os.path.splitext(name)[0]
        save_path = os.path.join('stored_embeds', 'files', name_without_extension)
        db.save_local(save_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing embeddings: {str(e)}")
    
    return {
        "message": "Scraped content and stored embeddings successfully",
        "content": content
    }


