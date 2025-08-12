from fastapi import Depends

from sqlalchemy.orm import Session
from datetime import timedelta,datetime
from .models import User
from .schemas import UserCreate,UserUpdate

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import jwt,JWTError
from database import get_db
from config import settings
from logger import log_security_event
from security_utils import account_protection, sanitizer

bcyrpt_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth2_bearer=OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

#exixting user check with proper SQL injection protection
async def existing_user(db:Session,username:str,email:str):
    # Sanitize inputs to prevent SQL injection
    username = username.strip() if username else ""
    email = email.strip() if email else ""
    
    # Use parameterized queries (SQLAlchemy ORM provides this by default)
    db_user_username = None
    db_user_email = None
    
    if username:
        db_user_username=db.query(User).filter(User.username==username).first()
    if email:
        db_user_email=db.query(User).filter(User.email==email).first()
    
    return db_user_username or db_user_email

#create access token
async def create_access_token(username:str, id:int):
    encode={"sub":username,"id":id}
    expires=datetime.utcnow()+timedelta(minutes=settings.token_expiration_minutes)
    encode.update({"exp":expires})
    return jwt.encode(encode,settings.secret_key,algorithm=settings.algorithm)
  
#get user from token
async def get_current_user(db:Session=Depends(get_db), token:str=Depends(oauth2_bearer)):
    try:
      payload=jwt.decode(token,settings.secret_key,algorithms=[settings.algorithm])
      username:str=payload.get("sub")
      id:int=payload.get("id")
      expires:datetime=payload.get("exp")
      if expires and datetime.fromtimestamp(expires)<datetime.utcnow():
        log_security_event("expired_token", {"username": username})
        return None
      if username is None or id is None:
        log_security_event("invalid_token", {"reason": "Missing username or id"})
        return None
      user = db.query(User).filter(User.id==id).first()
      if not user:
        log_security_event("user_not_found", {"username": username, "user_id": id})
      return user
    except JWTError as e:
      log_security_event("invalid_token", {"reason": str(e)})
      return None

#get user from user_id
async def get_user_from_id(db:Session, user_id:int):
    return db.query(User).filter(User.id==user_id).first()

#create new user
async def create_user(db:Session, user:UserCreate):
  # Additional sanitization at service layer (defense in depth)
  sanitized_email = sanitizer.sanitize_html(user.email.lower().strip())
  sanitized_username = sanitizer.sanitize_html(user.username.lower().strip())
  sanitized_name = sanitizer.sanitize_html(user.name) if user.name else None
  sanitized_bio = sanitizer.sanitize_html(user.bio) if user.bio else None
  sanitized_location = sanitizer.sanitize_html(user.location) if user.location else None
  sanitized_profile_pic = sanitizer.sanitize_html(user.profile_pic) if user.profile_pic else None
  
  db_user=User(
    email=sanitized_email,
    username=sanitized_username,
    hashed_password=bcyrpt_context.hash(user.hashed_password),
    dob=user.dob or None,
    gender=user.gender or None,
    bio=sanitized_bio,
    location=sanitized_location,
    profile_pic=sanitized_profile_pic,
    name=sanitized_name
  )
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user
  
  
  
#auth - Authenticate user with account lockout protection and SQL injection prevention
async def authenticate(db:Session, username:str, password:str, client_ip: str = None):   
    # Input validation and sanitization for SQL injection prevention
    if not username or not password:
        log_security_event("login_failed", {
            "username": username or "EMPTY",
            "ip": client_ip,
            "reason": "Empty username or password"
        })
        return {"locked": False, "user": None}
    
    # Strip and validate input length
    username = username.strip()
    password = password.strip()
    
    if len(username) > 50 or len(password) > 200:  # Prevent overly long inputs
        log_security_event("login_failed", {
            "username": username[:50],  # Log only first 50 chars
            "ip": client_ip,
            "reason": "Input too long - potential attack"
        })
        return {"locked": False, "user": None}
    
    # Check for SQL injection patterns
    sql_patterns = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_", "UNION", "SELECT", "DROP", "DELETE", "INSERT", "UPDATE"]
    for pattern in sql_patterns:
        if pattern.upper() in username.upper() or pattern.upper() in password.upper():
            log_security_event("sql_injection_attempt", {
                "username": username,
                "ip": client_ip,
                "reason": f"SQL injection pattern detected: {pattern}"
            })
            return {"locked": False, "user": None}
    
    # Check if account/IP is locked
    if account_protection.is_locked(username):
        log_security_event("account_locked_attempt", {
            "username": username,
            "ip": client_ip,
            "reason": "Account locked due to too many failed attempts"
        })
        return {"locked": True, "user": None}
    
    db_user=await existing_user(db, username, "")
    if not db_user:
        # Record failed attempt
        account_protection.record_failed_attempt(username)
        log_security_event("login_failed", {
            "username": username,
            "ip": client_ip,
            "reason": "User not found"
        })
        return {"locked": False, "user": None}
    
    if not bcyrpt_context.verify(password, db_user.hashed_password):
        # Record failed attempt
        should_lock = account_protection.record_failed_attempt(username)
        log_security_event("login_failed", {
            "username": username,
            "ip": client_ip,
            "reason": "Invalid password",
            "locked": should_lock
        })
        return {"locked": should_lock, "user": None}
    
    # Successful login - clear failed attempts
    account_protection.record_successful_login(username)
    log_security_event("login_success", {
        "username": username,
        "user_id": db_user.id,
        "ip": client_ip
    })
    
    return {"locked": False, "user": db_user}

#update user
async def update_user(db:Session, db_user:User, user:UserUpdate):
    # Additional sanitization at service layer (defense in depth)
    db_user.name = sanitizer.sanitize_html(user.name) if user.name else None
    db_user.dob = user.dob
    db_user.gender = user.gender
    db_user.bio = sanitizer.sanitize_html(user.bio) if user.bio else None
    db_user.location = sanitizer.sanitize_html(user.location) if user.location else None
    db_user.profile_pic = sanitizer.sanitize_html(user.profile_pic) if user.profile_pic else None
    db.commit()






