from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv
import os
from datetime import datetime
from pathlib import Path
from database import init_db

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Manga Dubbing Platform",
    version="1.0.0",
    description="An AI-powered platform for automatically converting manga PDFs into dubbed videos using Gemini and ElevenLabs"
)

# Configure CORS
# Normalize allowed origins: split by comma, strip whitespace, filter empty strings
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# Configure CORS middleware with conditional credentials
is_wildcard = allowed_origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=not is_wildcard,  # False if using wildcard
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount static files directory with absolute path
static_dir = Path(__file__).resolve().parent / 'static'
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint returning API information"""
    return {
        "service": "AI Manga Dubbing Platform API",
        "version": "1.0.0",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring"""
    return {
        "status": "healthy",
        "service": "manga-dubbing-api",
        "timestamp": datetime.utcnow().isoformat()
    }

# Database initialization event
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    init_db()
    print("Database initialized successfully")

# Import and include routers
from routers import upload, process, download
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(process.router, prefix="/api", tags=["status"])
app.include_router(download.router, prefix="/api", tags=["download"])

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "main:app",  # Use import string instead of app instance for reload to work
        host=host,
        port=port,
        reload=True
    )