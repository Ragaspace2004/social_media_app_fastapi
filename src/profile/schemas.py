from pydantic import BaseModel
from typing import Optional, List

from auth.schemas import UserBase

class Profile(UserBase):
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
    