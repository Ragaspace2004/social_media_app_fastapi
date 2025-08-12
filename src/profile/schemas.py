from datetime import date
from pydantic import BaseModel,Field,field_validator
from typing import Optional, List

from auth.schemas import UserBase
from auth.enums import Gender
from security_utils import sanitizer

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
    
    @field_validator('name', 'bio', 'location', 'profile_pic')
    @classmethod
    def sanitize_fields(cls, v):
        if v is not None:
            v = v.strip()
            v = sanitizer.sanitize_html(v)
        return v
    
    class Config:
        from_attributes =True
        
class UserSchema(UserBase):  #for efficient frontend delivery 
    username: str
    name: Optional[str] = None
    email:Optional[str]=None
    profile_pic: Optional[str] = None
    
    @field_validator('name', 'profile_pic')
    @classmethod
    def sanitize_fields(cls, v):
        if v is not None:
            v = v.strip()
            v = sanitizer.sanitize_html(v)
        return v
    
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
    