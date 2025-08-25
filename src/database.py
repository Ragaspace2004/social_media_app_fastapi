from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
import os

Engine = create_engine(settings.database_url, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)
Base=declarative_base()

def get_db():
  db=SessionLocal()
  try:
    yield db
  finally:
    db.close()
    
    
