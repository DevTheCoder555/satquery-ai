from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

# main.py is inside:
# backend/app/main.py
#
# We want:
# backend/uploads/

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="SatQuery AI",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATIC FILES
# ============================================================

app.mount(
    "/api/uploads",
    StaticFiles(directory=str(UPLOAD_DIR)),
    name="uploads"
)


# ============================================================
# IMPORT ROUTERS
# ============================================================

from app.api.upload import router as upload_router
from app.api.analysis import router as analysis_router


# ============================================================
# INCLUDE ROUTERS
# ============================================================

app.include_router(
    upload_router,
    prefix="/api"
)

app.include_router(
    analysis_router,
    prefix="/api"
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():
    return {
        "message": "SatQuery AI Backend",
        "version": "1.0.0"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }