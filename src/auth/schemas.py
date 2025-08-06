# schemas - for request and response models
from datetime import date,datetime
from pydantic import BaseModel
from typing import Optional
from .enums import Gender

class UserBase(BaseModel):
  email:str
  username:str
  name:str
  dob:Optional[date]=None
  gender:Optional[Gender]=None
  bio:Optional[str]=None
  location:Optional[str]=None
  profile_pic:Optional[str]=None
  
  
class UserCreate(UserBase):
  hashed_password:str
  
class UserUpdate(UserBase):
  name:str
  dob:Optional[date]=None
  gender:Optional[Gender]=None
  bio:Optional[str]=None
  location:Optional[str]=None
  profile_pic:Optional[str]=None
    
class User(UserBase):
  id:int
  created_at:datetime
  
  class Config:
    from_attributes = True
    
  
