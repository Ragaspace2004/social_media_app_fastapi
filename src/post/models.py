from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Date,Table
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.sql import func
from database import Base

#assosiation table for many-to-many relationship between posts and hashtags

post_hashtags=Table(
  "post_hashtags",
  Base.metadata,
  Column("post_id", Integer, ForeignKey("posts.id")),
  Column("hashtag_id", Integer, ForeignKey("hashtags.id"))
)

#association table for many-to-many relationship between users and posts
post_likes=Table(
  "post_likes",
  Base.metadata,
  Column("user_id", Integer, ForeignKey("user.id")),
  Column("post_id", Integer, ForeignKey("posts.id"))
)


class Post(Base):
  __tablename__ = "posts"
  id =Column(Integer,primary_key=True,index=True)
  content=Column(String(255),unique=True)
  image=Column(String(255))
  location=Column(String(255))
  created_at=Column(DateTime, default=func.now()) 
  likes_count=Column(Integer, default=0)
  
  author_id=Column(Integer,ForeignKey("user.id"))
  author=relationship("auth.models.User",back_populates="posts")  
  hashtags=relationship("Hashtag",secondary=post_hashtags,back_populates="posts")
  liked_by_users=relationship("auth.models.User",secondary=post_likes,back_populates="liked_posts")
  
  
class Hashtag(Base):
  __tablename__ = "hashtags"
  id =Column(Integer,primary_key=True,index=True)
  name=Column(String(255),index=True)
  
  posts=relationship("Post",secondary=post_hashtags,back_populates="hashtags")

  
  