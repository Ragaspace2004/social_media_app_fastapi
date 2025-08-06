from fastapi import FastAPI,APIRouter
from database import Base, Engine
from api import router

app=FastAPI(
    title="Social Media API",
    description="API for a social media application",
    version="1.0",
)
Base.metadata.create_all(bind=Engine)

app.include_router(router)
