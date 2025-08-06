from pydantic import BaseModel
from datetime import datetime

class Hashtag(BaseModel):
    id: int
    name:str
    
class PostCreate(BaseModel):
    content: str
    image: str = None
    location: str = None

class Post(PostCreate):
    id: int
    author_id:int
    likes_count:int=0
    created_at: datetime
    
    class Config:
      orm_mode = True