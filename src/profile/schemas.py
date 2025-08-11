from datetime import date
from pydantic import BaseModel,Field
from typing import Optional, List

from auth.schemas import UserBase
from auth.enums import Gender

class Profile(BaseModel):
    username:str = Field(..., min_length=3, max_length=30, pattern="^[a-zA-Z0-9_]+$")
    name:str 
    dob:Optional[date]=None
    gender:Optional[Gender]=None
    bio:Optional[str]=Field(None,max_length=1000, description="User bio")
    location:Optional[str]=Field(None,max_length=100, description="User location")
    profile_pic:Optional[str]=Field(None,max_length=100, description="User profile picture")
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
    
    class Config:
        from_attributes =True
        
class UserSchema(UserBase):  #for efficient frontend delivery 
    username: str
    name: Optional[str] = None
    email:Optional[str]=None
    profile_pic: Optional[str] = None
    
    class Config:
        from_attributes = True 
        
class FollowingList(BaseModel):
    following: List[UserSchema]=[]
    class Config:
        from_attributes = True 
    
class FollowersList(BaseModel):
    followers: List[UserSchema]=[]
    class Config:
        from_attributes = True 
    