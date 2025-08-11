from fastapi import FastAPI,APIRouter,Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from database import Base, Engine
from api import router
from config import settings
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from rate_limiter import general_rate_limit

@asynccontextmanager
async def lifespan(app:FastAPI):
    print("Starting FastAPI application")
    # Create database tables
    Base.metadata.create_all(bind=Engine)
    print("Database tables created successfully")
    yield
    print("Shutting down FastAPI application")
    

app=FastAPI(
    title="Social Media API",
    description="API for a social media application",
    version="1.0",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
    } # to keep user logged in
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

@app.exception_handler(Exception)
async def safe_exception_handler(request: Request, exc: Exception):
    #Catch all unhandled exceptions and return safe messages
    import logging
    logging.error(f"Unhandled error at {request.url.path}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "Please try again later"}
    )

# CORS middleware - CORS refers to the situations when a frontend running in a browser has JavaScript code that communicates with a backend, and the backend is in a different "origin" than the frontend.  Supports secure cross-origin requests and data transfers between browsers and servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(router)

# Add a root endpoint with rate limiting
@app.get("/")
async def root(request: Request, _: bool = Depends(general_rate_limit)):
    """Root endpoint with rate limiting for DDoS protection"""
    return {"message": "Social Media API", "version": "1.0", "status": "active"}
