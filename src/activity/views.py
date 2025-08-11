from fastapi import APIRouter,Depends,status
from sqlalchemy.orm import Session
from database import get_db
from .service import get_activity_by_username
from auth.service import get_current_user
from auth.schemas import User
from rate_limiter import api_rate_limit


router=APIRouter(prefix="/activity",tags=["activity"])

# get user activity by username
@router.get("/user")
async def activity(_: bool = Depends(api_rate_limit), user:User=Depends(get_current_user), page:int=1, limit:int=10, db:Session=Depends(get_db)):
    username=user.username
    return await get_activity_by_username(db,username,page,limit)


  

