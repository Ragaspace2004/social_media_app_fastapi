from fastapi import APIRouter,status,Depends,HTTPException
from sqlalchemy.orm import Session

from database import get_db
from .schemas import Profile,FollowingList,FollowersList
from .service import follow_svc,unfollow_svc,get_followers_svc,get_following_svc
from auth.service import existing_user, get_current_user

router = APIRouter(prefix="/profile",tags=["Profile"])

@router.get("/user/{username}",response_model=Profile)
async def profile(username:str,db:Session=Depends(get_db)):
    db_user=await existing_user(db,username,"")
    if not db_user:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    profile=Profile.model_validate(db_user)
    return profile
  
@router.post("/follow/{username}",status_code=status.HTTP_204_NO_CONTENT)
async def follow(username:str,token:str,db:Session=Depends(get_db)):
    db_user=await get_current_user(db,token)
    if not db_user:
       raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authenticated")
    res=await follow_svc(db,db_user.username,username)
    if not res:
       raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="could not follow")
     
@router.post("/unfollow/{username}",status_code=status.HTTP_204_NO_CONTENT)
async def unfollow(username:str,token:str,db:Session=Depends(get_db)):
    db_user=await get_current_user(db,token)
    if not db_user:
       raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authenticated")
    res=await unfollow_svc(db,db_user.username,username)
    
    if not res:
       raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="could not unfollow")
     
@router.get("/followers",response_model=FollowersList)
async def get_followers(token:str,db:Session=Depends(get_db)):
    current_user= await get_current_user(db,token)
    if not current_user:
       raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    return await get_followers_svc(db,current_user.id)
     
# get following
@router.get("/following",response_model=FollowingList)
async def get_following(token:str,db:Session=Depends(get_db)):
    current_user= await get_current_user(db,token)
    if not current_user:
       raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    return await get_following_svc(db,current_user.id)
    
    
    