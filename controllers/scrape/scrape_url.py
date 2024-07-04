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
import json
# https://www.orimi.com/pdf-test.pdf
# https://morth.nic.in/sites/default/files/dd12-13_0.pdf
router = APIRouter()

os.makedirs('stored_embeds/urls', exist_ok=True)

mapping_file = os.path.join('stored_embeds', 'url_mapping.json')
if os.path.exists(mapping_file):
    with open(mapping_file, 'r') as f:
        url_to_dir = json.load(f)
else:
    url_to_dir = {}

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
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.split_documents(documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scraping content: {str(e)}")
    
    try:
        embeddings = OpenAIEmbeddings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")
    
    if url in url_to_dir:
        save_dir = url_to_dir[url]
        embeddings_exist = True

        try:
            db = FAISS.load_local(save_dir, embeddings, allow_dangerous_deserialization=True)
            # Add new documents to the existing index
            db.add_documents(docs)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading existing embeddings: {str(e)}")
    else:
        save_dir = os.path.join('stored_embeds', 'urls', name)
        os.makedirs(save_dir, exist_ok=True)
        url_to_dir[url] = save_dir
        embeddings_exist = False

        # Create new FAISS index with the documents
        try:
            db = FAISS.from_documents(docs, embeddings)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating embeddings: {str(e)}")
        
        # Save the updated URL to directory mapping
        with open(mapping_file, 'w') as f:
            json.dump(url_to_dir, f)

    try:
        db.save_local(save_dir)
        if embeddings_exist:
            return {"message": "The embeddings for the provided URL exist, new embeddings added to the existing folder"}
        else:
            return {"message": "Scraped content and stored embeddings successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing embeddings: {str(e)}")

