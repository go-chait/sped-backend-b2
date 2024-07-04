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
import hashlib
import json
from datetime import datetime

router = APIRouter()

os.makedirs('stored_embeds/files', exist_ok=True)

# Set the path for the hash to directory mapping file inside stored_embeds
mapping_file = os.path.join('stored_embeds', 'file_mapping.json')
if os.path.exists(mapping_file):
    with open(mapping_file, 'r') as f:
        hash_to_dir = json.load(f)
else:
    hash_to_dir = {}

class FileRequest(BaseModel):
    name: str
    content_type: str
    content: str 

def compute_hash(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()

@router.post('/scrape-and-store-file', response_model=dict)
@version(1)
async def scrape_and_store(request: FileRequest):
    name = request.name
    content_type = request.content_type
    content = request.content
    
    if content_type.lower() != 'pdf':
        raise HTTPException(status_code=400, detail="Unsupported content type. ('pdf' is allowed)")
    
    try:
        file_data = base64.b64decode(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error decoding file content: {str(e)}")
    
    file_hash = compute_hash(file_data)
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing temp file: {str(e)}")
    
    try:
        loader = PyPDFLoader(temp_file_path)
        pages = loader.load_and_split()
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
    
    if file_hash in hash_to_dir:
        save_dir = hash_to_dir[file_hash]
        embeddings_exist = True

        # Load existing FAISS index and add new documents
        try:
            db = FAISS.load_local(save_dir, embeddings, allow_dangerous_deserialization=True)
            db.add_documents(docs)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading or updating existing embeddings: {str(e)}")
    else:
        name_without_extension = os.path.splitext(name)[0]
        save_dir = os.path.join('stored_embeds', 'files', name_without_extension)
        os.makedirs(save_dir, exist_ok=True)
        hash_to_dir[file_hash] = save_dir
        embeddings_exist = False

        # Create new FAISS index with the documents
        try:
            db = FAISS.from_documents(docs, embeddings)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating embeddings: {str(e)}")
        
        # Save the updated hash to directory mapping
        with open(mapping_file, 'w') as f:
            json.dump(hash_to_dir, f)

    try:
        # Save the FAISS index to the directory
        db.save_local(save_dir)
        if embeddings_exist:
            return {"message": "The embeddings for the provided file exist, new embeddings added to the existing folder"                     }
        else:
            return {"message": "Scraped content and stored embeddings successfully"                     }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing embeddings: {str(e)}")
