from fastapi import HTTPException, Depends, APIRouter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from fastapi_versioning import version
import os
import base64
import tempfile
from langchain_text_splitters import CharacterTextSplitter
from controllers.scrape.table import get_mapping, set_mapping, update_data_table
from core.security.security import require_auth
from db.mongodb import FileMappings
from models.scrape import FileRequest

router = APIRouter()

os.makedirs('stored_embeds', exist_ok=True)

@router.post('/scrape-and-store-file')
@version(1)
async def scrape_and_store_file(request: FileRequest, auth: dict = Depends(require_auth)):
    name = request.name
    content_type = request.content_type
    content = request.content
    
    if content_type.lower() != 'pdf':
        raise HTTPException(status_code=400, detail="Unsupported content type. ('pdf' is allowed)")
    
    try:
        file_data = base64.b64decode(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error decoding file content: {str(e)}")
    
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
        os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error scraping PDF content: {str(e)}")
    
    os.remove(temp_file_path)
    
    try:
        embeddings = OpenAIEmbeddings()
        save_dir = os.path.join('stored_embeds')
        
        if os.path.exists(os.path.join(save_dir, 'index.faiss')):
            #  Load existing FAISS index
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
        update_data_table(name, content_type, 'scraped', auth['userId'])
        return {"message": "Scraped content and stored embeddings successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating data table: {str(e)}")
