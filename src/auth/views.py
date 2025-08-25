from cmath import log
from fastapi import APIRouter, Depends,status,HTTPException,Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from .schemas import UserCreate, UserUpdate, User
from database import get_db
from .service import existing_user, create_access_token, get_current_user, get_user_from_id,authenticate,create_user as create_user_svc,update_user as update_user_svc
from logger import log_auth_success, log_auth_failed, log_error, log_user_action, log_unauthorized_access, get_client_ip, get_user_agent
from rate_limiter import auth_rate_limit, general_rate_limit

router =APIRouter(prefix="/auth",tags=["auth"])

#signup
@router.post("/register",status_code=status.HTTP_201_CREATED)
async def create_user(request:Request,user:UserCreate, _: bool = Depends(auth_rate_limit), db:Session=Depends(get_db)):
  #only 5 requests per minute for auth endpoints
  client_ip = get_client_ip(request)
  user_agent = get_user_agent(request)
  #exceptional handling
  
  try:
      db_user = await existing_user(db,user.username,user.email)
      if db_user:
         log_auth_failed(user.username, client_ip, "user already exists", user_agent)
         raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                        detail="Username or Email already exists")
      db_user=await create_user_svc(db,user)
      access_token=await create_access_token(user.username,db_user.id)
      log_auth_success(f"SIGNUP:{user.username}", client_ip, user_agent)
      return {"access_token":access_token,"token_type":"bearer","username":user.username}

  except HTTPException:
      raise  # Re-raise HTTP exceptions as-is
  except Exception as e:
      log_error(f"SIGNUP:{user.username}", str(e), "/auth/register", client_ip)
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Internal Server Error")
#login
@router.post("/login", status_code = status.HTTP_200_OK)
async def login(request: Request, _: bool = Depends(auth_rate_limit), form_data : OAuth2PasswordRequestForm=Depends(), db:Session=Depends(get_db)):
  #for logging
  client_ip = get_client_ip(request)
  user_agent = get_user_agent(request)
  username = form_data.username
  
  try:
      auth_result = await authenticate(db, form_data.username, form_data.password, client_ip)
      
      # Check if account is locked
      if auth_result.get("locked"):
          log_auth_failed(username, client_ip, "account locked due to too many failed attempts", user_agent)
          raise HTTPException(
              status_code=status.HTTP_423_LOCKED,
              detail="Account locked due to too many failed attempts. Please try again later."
          )
      
      # Check if authentication failed
      if not auth_result.get("user"):
         log_auth_failed(username, client_ip, "incorrect username or password", user_agent)
         raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="incorrect username or password"
          )
      
      db_user = auth_result["user"]
      access_token=await create_access_token(db_user.username,db_user.id)
      log_auth_success(f"LOGIN:{username}", client_ip, user_agent)
      return {"access_token":access_token,"token_type":"bearer"}
  except HTTPException:
      raise  # Re-raise HTTP exceptions as-is
  except Exception as e:
      log_error(f"Login error for {username}", str(e), "/auth/login", client_ip)
      raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )
#current_user -->replaced the feature of passing tokens as parameters with dependency injection
@router.get("/profile",status_code=status.HTTP_200_OK,response_model=User)
async def current_user(request: Request, _: bool = Depends(general_rate_limit), db_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
  # db_user=await get_current_user(db,token)
  if not db_user:
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    log_unauthorized_access(client_ip, "/auth/profile", "invalid or expired token", user_agent)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token")
  return db_user

#update_user --> replaced the feature of passing tokens as parameters with dependency injection

@router.put("/profile",status_code=status.HTTP_204_NO_CONTENT)
async def update_user(request:Request,user_update:UserUpdate, _: bool = Depends(general_rate_limit), db_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
  client_ip = get_client_ip(request)
  user_agent = get_user_agent(request)
  try:
      log_user_action(db_user.username, "profile_update", "profile updated successfully", user_agent)
      return await update_user_svc(db,db_user,user_update)
  except Exception as e:
      log_error(f"Profile update error for {db_user.username}", str(e), "/auth/profile", client_ip)
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="Profile update failed"
      )
