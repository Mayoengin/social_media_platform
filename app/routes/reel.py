from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session, select
from typing import Optional
from sqlalchemy import func
import os
import shutil
import uuid

from app.database import get_session
from app.model import User, Reel, ReelCreate, ReelResponse, ReelWithOwnerResponse, UserInfo, ReelVote, Comment, CommentCreate, CommentResponse
from app.routes.auth import get_current_user

router = APIRouter(
    prefix="/reels",
    tags=["reels"]
)

# Configure file storage
UPLOAD_DIR = "uploads/reels"
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB limit (adjust as needed)
ALLOWED_EXTENSIONS = {"mp4", "mov", "avi"}

# Helper to ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@router.post("/", response_model=ReelResponse, status_code=status.HTTP_201_CREATED)
async def create_reel(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    video_file: UploadFile = File(...),
    thumbnail: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Validate file size and type
    if not allowed_file(video_file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video format. Allowed formats: mp4, mov, avi"
        )
    
    # Create unique filename
    video_filename = f"{uuid.uuid4()}_{video_file.filename}"
    video_path = os.path.join(UPLOAD_DIR, video_filename)
    
    # Save video file
    try:
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading video: {str(e)}"
        )
    
    # Handle thumbnail if provided
    thumbnail_url = None
    if thumbnail:
        thumbnail_filename = f"{uuid.uuid4()}_{thumbnail.filename}"
        thumbnail_path = os.path.join(UPLOAD_DIR, thumbnail_filename)
        try:
            with open(thumbnail_path, "wb") as buffer:
                shutil.copyfileobj(thumbnail.file, buffer)
            thumbnail_url = f"/uploads/reels/{thumbnail_filename}"
        except Exception:
            # Continue even if thumbnail upload fails
            pass
    
    # Create new reel record
    new_reel = Reel(
        title=title,
        description=description,
        video_url=f"/uploads/reels/{video_filename}",
        thumbnail_url=thumbnail_url,
        duration=110,  # Set a default of 1:50 (110 seconds) - ideally this would be extracted from the video
        owner_id=current_user.id
    )
    
    session.add(new_reel)
    session.commit()
    session.refresh(new_reel)
    
    # Create response
    reel_response = ReelResponse(
        id=new_reel.id,
        title=new_reel.title,
        description=new_reel.description,
        video_url=new_reel.video_url,
        thumbnail_url=new_reel.thumbnail_url,
        duration=new_reel.duration,
        created_at=new_reel.created_at,
        owner_id=new_reel.owner_id,
        votes=0
    )
    
    return reel_response


@router.get("/", response_model=list[ReelWithOwnerResponse])
def get_reels(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    skip: int = 0,
    search: Optional[str] = ""
):
    # Join Reel with User and count votes
    query = select(
        Reel, 
        func.count(ReelVote.reel_id).label("votes")
    ).join(
        User, 
        Reel.owner_id == User.id, 
        isouter=False
    ).join(
        ReelVote, 
        ReelVote.reel_id == Reel.id, 
        isouter=True
    ).group_by(
        Reel.id, User.id
    )
    
    if search:
        query = query.filter(Reel.title.contains(search))
    
    # Apply pagination
    results = session.exec(query.offset(skip).limit(limit)).all()
    
    # Format the results
    reels_with_details = []
    for reel, votes in results:
        # Get the owner
        owner = session.get(User, reel.owner_id)
        owner_info = UserInfo(id=owner.id, username=owner.username)
        
        # Create the response object
        reel_response = ReelWithOwnerResponse(
            id=reel.id,
            title=reel.title,
            description=reel.description,
            video_url=reel.video_url,
            thumbnail_url=reel.thumbnail_url,
            duration=reel.duration,
            created_at=reel.created_at,
            owner_id=reel.owner_id,
            votes=votes,
            owner=owner_info
        )
        
        reels_with_details.append(reel_response)
    
    return reels_with_details

@router.get("/{id}", response_model=ReelWithOwnerResponse)
def get_reel_by_id(
    id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Query that joins Reel with ReelVote to count votes
    query = select(
        Reel, 
        func.count(ReelVote.reel_id).label("votes")
    ).join(
        ReelVote, 
        ReelVote.reel_id == Reel.id, 
        isouter=True
    ).filter(Reel.id == id).group_by(Reel.id)
    
    result = session.exec(query).first()
    
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No reel with ID {id}")
    
    reel, votes = result
    
    # Get the owner
    owner = session.get(User, reel.owner_id)
    owner_info = UserInfo(id=owner.id, username=owner.username)
    
    # Create the response with owner and votes
    reel_response = ReelWithOwnerResponse(
        id=reel.id,
        title=reel.title,
        description=reel.description,
        video_url=reel.video_url,
        thumbnail_url=reel.thumbnail_url,
        duration=reel.duration,
        created_at=reel.created_at,
        owner_id=reel.owner_id,
        votes=votes,
        owner=owner_info
    )
    
    return reel_response

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reel(
    id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Retrieve reel by ID
    reel = session.get(Reel, id)
    if not reel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reel with ID {id} not found")
    
    # Check if the current user is the owner of the reel
    if reel.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this reel")
    
    # Delete associated files
    if reel.video_url:
        try:
            video_path = os.path.join(os.getcwd(), reel.video_url.lstrip('/'))
            if os.path.exists(video_path):
                os.remove(video_path)
        except Exception:
            # Continue with deletion even if file removal fails
            pass
            
    if reel.thumbnail_url:
        try:
            thumbnail_path = os.path.join(os.getcwd(), reel.thumbnail_url.lstrip('/'))
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except Exception:
            pass
    
    session.delete(reel)
    session.commit()
    return