from sqlalchemy import Column, Integer, String, DateTime, Date, Enum, ForeignKey
from sqlalchemy.sql import func
from database import Base
from .enums import Gender
from sqlalchemy.orm import relationship
from post.models import Post

class Follow(Base):
  __tablename__ = "follow"
  follower_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
  following_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
  
  follower=relationship("User",foreign_keys=[follower_id],back_populates="following")
  following=relationship("User",foreign_keys=[following_id],back_populates="followers")

class User(Base):
  __tablename__="user"
  id = Column(Integer,primary_key=True, index=True) 
  email=Column(String(255),unique=True)             
  username=Column(String(50),unique=True)            
  name=Column(String(100))                          
  hashed_password=Column(String(255), nullable=False) 
  created_at=Column(DateTime, default=func.now()) 
  dob=Column(Date, nullable=True)
  gender=Column(Enum(Gender))
  profile_pic=Column(String(500), nullable=True)
  bio=Column(String(1000), nullable=True)
  location=Column(String(200), nullable=True)
  
  posts=relationship(Post,back_populates="author")
  liked_posts=relationship(Post,secondary="post_likes",back_populates="liked_by_users")
  
  followers=relationship(Follow,foreign_keys=[Follow.following_id],back_populates="following")
  following=relationship(Follow,foreign_keys=[Follow.follower_id],back_populates="follower")
  followers_count = Column(Integer, default=0)
  following_count = Column(Integer, default=0)
  