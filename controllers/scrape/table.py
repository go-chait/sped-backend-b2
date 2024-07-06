from typing import List, Dict
from fastapi import APIRouter
from fastapi_versioning import version
from datetime import datetime
from db.mongodb import DataTable

router = APIRouter()

def get_mapping(collection, key):
    mapping = collection.find_one({"key": key})
    if mapping:
        return mapping["value"]
    return None


def set_mapping(collection, key, value):
    collection.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)
    
    
def update_data_table(name: str, content_type: str, status: str, user_ID: str):
    entry = {
        "name": name,
        "userID": user_ID,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "type": content_type,
        "status": status
    }
    DataTable.insert_one(entry)

@router.get('/data-table', response_model=List[Dict])
@version(1)
async def get_data_table():
    return list(DataTable.find({}, {"_id": 0}))

