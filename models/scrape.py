from pydantic import BaseModel

class UrlRequest(BaseModel):
    url: str
    name: str

class FileRequest(BaseModel):
    name: str
    content_type: str
    content: str 
