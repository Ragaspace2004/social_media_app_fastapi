from fastapi import APIRouter,status,Depends,HTTPException
from sqlalchemy.orm import Session
from database import get_db
from .schemas import Profile,FollowingList,FollowersList
from .service import follow_svc,unfollow_svc,get_followers_svc,get_following_svc,check_follow_svc
from auth.schemas import User
from auth.service import existing_user, get_current_user
from rate_limiter import general_rate_limit, api_rate_limit

router = APIRouter(prefix="/profile",tags=["Profile"])

@router.get("/user/{username}",response_model=Profile)
async def profile(username:str, _: bool = Depends(api_rate_limit), db:Session=Depends(get_db)):
    db_user=await existing_user(db,username,"")
    if not db_user:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    profile=Profile.model_validate(db_user)
    return profile
  
@router.post("/follow/{username}",status_code=status.HTTP_204_NO_CONTENT)
async def follow(username:str, _: bool = Depends(general_rate_limit), db_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    if not db_user:
       raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authenticated")
    res=await follow_svc(db,db_user.username,username)
    if not res:
       raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="could not follow")
     
@router.post("/unfollow/{username}",status_code=status.HTTP_204_NO_CONTENT)
async def unfollow(username:str, _: bool = Depends(general_rate_limit), db_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    if not db_user:
       raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authenticated")
    res=await unfollow_svc(db,db_user.username,username)
    
    if not res:
       raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="could not unfollow")

# get followers     
@router.get("/followers",response_model=FollowersList)
async def get_followers(_: bool = Depends(api_rate_limit), current_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    if not current_user:
       raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    return await get_followers_svc(db,current_user.id)
     
# get following
@router.get("/following",response_model=FollowingList)
async def get_following(_: bool = Depends(api_rate_limit), current_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    if not current_user:
       raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    return await get_following_svc(db,current_user.id)
 
# get following by username
@router.get("/following/{username}",response_model=FollowingList)
async def get_following_by_username(username:str, _: bool = Depends(api_rate_limit), current_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    if current_user == username:
       return await get_following_svc(db,current_user.id)
    following_activity = await check_follow_svc(db,current_user.username,username)
    target_user = await existing_user(db, username, "")
    if not following_activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not followed or your follower")
    return await get_following_svc(db, target_user.id)
 

#get followers by username
@router.get("/followers/{username}",response_model=FollowersList)
async def get_followers_by_username(username:str, _: bool = Depends(api_rate_limit), current_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    if current_user == username:
       return await get_followers_svc(db,current_user.id)
    following_activity = await check_follow_svc(db,current_user.username,username)
    target_user = await existing_user(db, username, "")
    if not following_activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not mutually following")
    return await get_followers_svc(db, target_user.id)  
 
 
    
    
    
    
    