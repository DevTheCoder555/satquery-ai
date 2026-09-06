from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="SatQuery AI", version="1.0.0")

# CORS middleware - configure based on environment
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Import routers
from app.api.upload import router as upload_router
from app.api.analysis import router as analysis_router

# Include routers
app.include_router(upload_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "SatQuery AI Backend", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
