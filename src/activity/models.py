from sqlalchemy import Column, Integer, String, ForeignKey,DateTime
from sqlalchemy.sql import func
from datetime import datetime
from database import Base

class Activity(Base):
   __tablename__="activity"
   id = Column(Integer,primary_key=True)
   username=Column(String(255),nullable=False)
   timestamp=Column(DateTime,default=func.now())
   liked_post_id=Column(Integer)
   username_liked=Column(String(255))
   liked_post_image=Column(String(255))
   
   followed_username=Column(String(255))
   followed_user_pic=Column(String(255))
   
   
   
   
   
