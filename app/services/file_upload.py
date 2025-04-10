# app/services/file_upload.py
import os
import uuid
from fastapi import UploadFile
import urllib.parse
import shutil
def generate_unique_filename(filename):
    """Generate a unique filename to prevent overwriting"""
    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    return unique_filename

def save_uploaded_file(file: UploadFile, upload_dir: str) -> str:
    """
    Save an uploaded file to the specified directory with a unique filename.
    
    Args:
        file: The uploaded file
        upload_dir: The directory to save the file in
        
    Returns:
        The unique filename (without the directory)
    """
    # Create directory if it doesn't exist
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename with UUID to prevent overwriting
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Full path to save the file
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return just the unique filename, not the full path
    return unique_filename


def get_file_url(filename: str, upload_dir: str = None) -> str:
    """
    Get the URL path for an uploaded file.
    
    Args:
        filename: The unique filename
        upload_dir: The directory where the file is saved (optional)
        
    Returns:
        The URL path to access the file
    """
    # If upload_dir is provided, use it; otherwise, just use the filename
    # Important: Make sure we return a consistent format starting with '/'
    if upload_dir:
        # Ensure we don't have double slashes
        if upload_dir.startswith('/'):
            return f"{upload_dir}/{filename}"
        else:
            return f"/{upload_dir}/{filename}"
    else:
        # If no directory specified, just return the filename with leading slash
        return f"/{filename}"