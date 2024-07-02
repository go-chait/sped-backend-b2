from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from typing import List
from fastapi import Depends, APIRouter, Query, status, Body
from fastapi_versioning import version
import os 

router = APIRouter()

class ScrapeRequest(BaseModel):
    url: str
    name: str

@router.post('/scrape-and-store-url', response_model=dict)
@version(1)
async def scrape_and_store(request: ScrapeRequest):
    url = request.url
    name = request.name
    
    try:
        loader = WebBaseLoader(url)
        documents = loader.load()
        content = "\n".join(doc.page_content for doc in documents)
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)        
        docs = text_splitter.split_documents(documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scraping content: {str(e)}")
    
    try:
        embeddings = OpenAIEmbeddings()
        db = FAISS.from_documents(docs, embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")
    
    try:
        save_path = os.path.join('stored_embeds', 'urls', name)
        db.save_local(save_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing embeddings: {str(e)}")
    
    return {"message": "Scraped content and stored embeddings successfully",
            "content": content
            }

# @router.get('/')
# @version(1)
# async def home():
#     return {"message": "Welcome to the API"}

