from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from utils.auth import get_current_user
import os
import shutil
import uuid
from datetime import datetime

router = APIRouter(prefix="/uploads", tags=["Uploads"])

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    try:
        # Generate a unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_url = f"/uploads/{unique_filename}"
        
        return {
            "success": True, 
            "data": {
                "url": file_url,
                "filename": file.filename,
                "size": os.path.getsize(file_path)
            }, 
            "message": "File uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
