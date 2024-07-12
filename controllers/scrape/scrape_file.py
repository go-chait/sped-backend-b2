from fastapi import HTTPException, Depends, APIRouter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from fastapi_versioning import version
import os
import base64
import tempfile
from langchain_text_splitters import CharacterTextSplitter
from controllers.scrape.table import update_data_table
from core.security.security import require_auth
from db.mongodb import Users
from models.scrape import FileRequest
from bson import ObjectId

router = APIRouter()

os.makedirs('stored_embeds', exist_ok=True)

@router.post('/scrape-and-store-file-admin')
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
            db = FAISS.load_local(save_dir, embeddings, allow_dangerous_deserialization=True)
            db.add_documents(docs)
        else:
            db = FAISS.from_documents(docs, embeddings)

        db.save_local(save_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing embeddings: {str(e)}")

    try:
        user =  Users.find_one({"_id":  ObjectId(auth['userId'])})
        if not user:
            print(f"User with ID {auth['userId']} not found.")
            raise HTTPException(status_code=404, detail="User not found")

        role = user.get('role', 'unknown')

        update_data_table(name, content_type, 'scraped', auth['userId'], role)
        return {"message": "Scraped content and stored embeddings successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating data table: {str(e)}")

@router.post('/scrape-and-store-file-user')
@version(1)
async def scrape_and_store_file(request: FileRequest, auth: dict = Depends(require_auth)):
    name = request.name
    content_type = request.content_type
    content = request.content
    # print("HI!")
    # Check if the authenticated user has the role "user"
    try:
        user =  Users.find_one({"_id": ObjectId(auth['userId'])})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        role = user.get('role', 'unknown')
        if role.lower() != 'user':
            raise HTTPException(status_code=403, detail="Access denied. Only users with the role 'user' can upload PDFs.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying user role: {str(e)}")

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

    # Create a directory named by the userId
    user_dir = os.path.join('stored_embeds', str(auth['userId']))
    os.makedirs(user_dir, exist_ok=True)

    try:
        embeddings = OpenAIEmbeddings()
        save_dir = user_dir

        if os.path.exists(os.path.join(save_dir, 'index.faiss')):
            db = FAISS.load_local(save_dir, embeddings, allow_dangerous_deserialization=True)
            db.add_documents(docs)
        else:
            db = FAISS.from_documents(docs, embeddings)

        db.save_local(save_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing embeddings: {str(e)}")

    try:
        # print("HIIIII!")
        update_data_table(name, content_type, 'scraped', auth['userId'], role)
        return {"message": "Scraped content and stored embeddings successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating data table: {str(e)}")
