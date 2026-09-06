from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid
import shutil

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_image(files: list[UploadFile] = File(...)):
    """Upload one or more satellite images"""
    uploaded_files = []

    for file in files:
        # Validate file type
        allowed_types = [".tif", ".tiff", ".png", ".jpg", ".jpeg", ".geotiff"]
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Use: {', '.join(allowed_types)}",
            )

        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = f"{unique_id}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        uploaded_files.append(
            {
                "filename": safe_filename,
                "original_name": file.filename,
                "path": str(file_path),
                "url": f"/uploads/{safe_filename}",
            }
        )

    return {"success": True, "files": uploaded_files, "count": len(uploaded_files)}


@router.get("/images")
async def list_images():
    """List all uploaded images"""
    images = []
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            images.append(
                {"filename": file_path.name, "url": f"/uploads/{file_path.name}"}
            )
    return {"images": images}
