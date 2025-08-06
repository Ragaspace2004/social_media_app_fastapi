from fastapi import Depends

from sqlalchemy.orm import Session
from datetime import timedelta,datetime
from .models import User
from .schemas import UserCreate,UserUpdate

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import jwt,JWTError

import os
from dotenv import load_dotenv
load_dotenv()

bcyrpt_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth2_bearer=OAuth2PasswordBearer(tokenUrl="auth/login")
SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
TOKEN_EXPIRATION_MINUTES=os.getenv("TOKEN_EXPIRATION_MINUTES")

#exixting user check
async def existing_user(db:Session,username:str,email:str):
    db_user_username=db.query(User).filter(User.username==username).first()
    db_user_email=db.query(User).filter(User.email==email).first()
    return db_user_username or db_user_email

#create access token
async def create_access_token(username:str, id:int):
    encode={"sub":username,"id":id}
    expires=datetime.utcnow()+timedelta(int(minutes=TOKEN_EXPIRATION_MINUTES))
    encode.update({"exp":expires})
    return jwt.encode(encode,SECRET_KEY,algorithm=ALGORITHM)
  
#get user from token
async def get_current_user(db:Session, token:str=Depends(oauth2_bearer)):
    try:
      payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
      username:str=payload.get("sub")
      id:int=payload.get("id")
      expires:datetime=payload.get("exp")
      if expires and datetime.fromtimestamp(expires)<datetime.utcnow():
        return None
      if username is None or id is None:
        return None
      return db.query(User).filter(User.id==id).first()
    except JWTError:
      return None

#get user from user_id
async def get_user_from_id(db:Session, user_id:int):
    return db.query(User).filter(User.id==user_id).first()
  
async def create_user(db:Session, user:UserCreate):
  db_user=User(
    email=user.email.lower().strip(),
    username=user.username.lower().strip(),
    hashed_password=bcyrpt_context.hash(user.hashed_password),
    dob=user.dob or None,
    gender=user.gender or None,
    bio=user.bio or None,
    location=user.location or None,
    profile_pic =user.profile_pic or None,
    name=user.name or None
  )
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user
  
  
  
#auth
async def authenticate(db:Session, username:str, password:str):
  db_user=await existing_user(db, username, "")
  if not db_user:
    return None
  if not bcyrpt_context.verify(password, db_user.hashed_password):
    return None
  return db_user

#update user
async def update_user(db:Session, db_user:User, user:UserUpdate):
    db_user.name = user.name
    db_user.dob = user.dob
    db_user.gender = user.gender
    db_user.bio = user.bio
    db_user.location = user.location
    db_user.profile_pic = user.profile_pic
    db.commit()






