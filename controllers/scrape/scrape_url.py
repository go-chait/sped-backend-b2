from fastapi import HTTPException, Depends, APIRouter
from pydantic import BaseModel
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from fastapi_versioning import version
import os
from controllers.scrape.table import get_mapping, set_mapping, update_data_table
from core.security.security import require_auth
from db.mongodb import UrlMappings
from models.scrape import UrlRequest

router = APIRouter()

os.makedirs('stored_embeds', exist_ok=True)

@router.post('/scrape-and-store-url', response_model=dict)
@version(1)
async def scrape_and_store_url(request: UrlRequest, auth: dict = Depends(require_auth)):
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
        save_dir = os.path.join('stored_embeds')
        
        if os.path.exists(os.path.join(save_dir, 'index.faiss')):
            # Load existing FAISS index
            db = FAISS.load_local(save_dir, embeddings, allow_dangerous_deserialization=True)
            # Add new documents and their embeddings to the existing FAISS index
            db.add_documents(docs)
        else:
            # Create a new FAISS index with the documents
            db = FAISS.from_documents(docs, embeddings)
        
        # Save the updated FAISS index
        db.save_local(save_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing embeddings: {str(e)}")
    
    try:
        update_data_table(name, 'url', 'scraped', auth['userId'])
        return {"message": "Scraped content and stored embeddings successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating data table: {str(e)}")
