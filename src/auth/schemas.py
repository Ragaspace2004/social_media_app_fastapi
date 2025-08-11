# schemas - for request and response models
from datetime import date,datetime
from pydantic import BaseModel,field_validator,Field,EmailStr
from typing import Optional
from .enums import Gender
import re
from security_utils import sanitizer

class UserBase(BaseModel):
  email:EmailStr = Field(...,description="Valid email address")
  username:str = Field(..., min_length=3, max_length=30, pattern="^[a-zA-Z0-9_]+$")
  name:str 
  dob:Optional[date]=None
  gender:Optional[Gender]=None
  bio:Optional[str]=Field(None,max_length=1000, description="User bio")
  location:Optional[str]=Field(None,max_length=100, description="User location")
  profile_pic:Optional[str]=Field(None,max_length=100, description="User profile picture")
  
  @field_validator('email','username','name', 'bio', 'location', 'profile_pic')
  @classmethod
  def sanitize_fields(cls, v):
      if v is not None:
         v = v.strip()
         v = sanitizer.sanitize_html(v)
      return v
     
  
class UserCreate(UserBase):
  hashed_password:str

  @field_validator('hashed_password')
  @classmethod
  def validate_password(cls, v):
    
      v = v.strip()
      if len(v) < 8:
        raise ValueError('Password must be at least 8 characters')
      if not re.search(r'[A-Z]', v):
         raise ValueError('Password must contain at least one uppercasletter')
      if not re.search(r'[a-z]', v):
         raise ValueError('Password must contain at least one lowercase letter')
      if not re.search(r'[0-9]', v):
         raise ValueError('Password must contain at least one number')
      if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
         raise ValueError('Password must contain at least one special character')
      if not sanitizer.sanitize_html(v):
         raise ValueError('Password contains unwanted symbols')

        # Common password usage prevention
      common_passwords = ['password', '123456', '123456789', 'qwerty', 'abc123']
      if v.lower() in common_passwords:
        raise ValueError('Use a strong Password')
        
      return v  


class UserUpdate(BaseModel):
  name:str
  dob:Optional[date]=None
  gender:Optional[Gender]=None
  bio:Optional[str]=None
  location:Optional[str]=None
  profile_pic:Optional[str]=None
  
  @field_validator('name', 'bio', 'location', 'profile_pic')
  @classmethod
  def sanitize_fields(cls, v):
      if v is not None:
         v = v.strip()
         v = sanitizer.sanitize_html(v)
      return v
    
class User(UserBase):
  id:int
  created_at:datetime
  
  class Config:
    from_attributes = True
    
  
