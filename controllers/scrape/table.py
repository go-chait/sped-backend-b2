from typing import List, Dict
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi_versioning import version
from datetime import datetime
from db.mongodb import DataTable, Users
from fastapi import HTTPException, Depends, APIRouter
from fastapi_versioning import version
from core.security.security import require_auth
from db.mongodb import DataTable  # Import the data table collection
from bson import ObjectId

router = APIRouter()

def get_mapping(collection, key):
    mapping = collection.find_one({"key": key})
    if mapping:
        return mapping["value"]
    return None


def set_mapping(collection, key, value):
    collection.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)
    
    
def update_data_table(name: str, content_type: str, status: str, user_ID: str, role):
    entry = {
        "name": name,
        "userID": user_ID,
        "role": role,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "type": content_type,
        "status": status
    }
    DataTable.insert_one(entry)

@router.get('/data-table', response_model=List[Dict])
@version(1)
async def get_data_table():
    return list(DataTable.find({}, {"_id": 0}))


@router.get('/view-admin-docs', response_model=dict)
@version(1)
async def view_admin_docs(auth: dict = Depends(require_auth)):
    try:
        user_id = auth['userId']
        user =  Users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        role = user.get('role', 'unknown')
        
        if role.lower() != 'admin':
            return JSONResponse(status_code=403, content={"message": "Sorry, you can't see admin documents."})
        
        admin_docs_cursor = DataTable.find({"role": "Admin"})
        admin_docs = []
        for doc in admin_docs_cursor:
            # Convert ObjectId to string for JSON serialization
            doc['_id'] = str(doc['_id'])
            admin_docs.append(doc)
        
        json_compatible_admin_docs = jsonable_encoder({"admin_docs": admin_docs})
        
        return JSONResponse(content=json_compatible_admin_docs)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


@router.get('/view-user-docs', response_model=dict)
@version(1)
async def view_user_docs(user_id: str, auth: dict = Depends(require_auth)):
    try:
        user =  Users.find_one({"_id": ObjectId(auth['userId'])})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # role = user.get('role', 'unknown')        
        # Allow admins to view any user's documents, otherwise restrict to own documents
        # if role.lower() != 'admin' and str(user_id) != str(auth['userId']):
        #     return JSONResponse(status_code=403, content={"message": "Access denied. You can only view your own documents."})
        
        user_docs_cursor = DataTable.find({"userID": user_id})
        
        user_docs = []
        for doc in user_docs_cursor:
            doc['_id'] = str(doc['_id'])
            user_docs.append(doc)
        
        json_compatible_user_docs = jsonable_encoder({"user_docs": user_docs})
        
        return JSONResponse(content=json_compatible_user_docs)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")
