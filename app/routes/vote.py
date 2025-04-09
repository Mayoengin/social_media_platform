from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, SQLModel
from app.database import get_session
from app.model import Post, Reel, Vote, User
from app.routes.auth import get_current_user
from typing import Optional

router = APIRouter(
    prefix="/vote",
    tags=["votes"]
)

class VoteRequest(SQLModel):
    post_id: Optional[int] = None
    reel_id: Optional[int] = None

@router.post("/", status_code=status.HTTP_201_CREATED)
def vote(
    vote_request: VoteRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Validate request - either post_id or reel_id must be provided, but not both
    if (vote_request.post_id is None and vote_request.reel_id is None) or \
       (vote_request.post_id is not None and vote_request.reel_id is not None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either post_id or reel_id must be provided, but not both"
        )
    
    # Handle post vote
    if vote_request.post_id is not None:
        post_id = vote_request.post_id
        
        # Check if post exists
        post = db.get(Post, post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
            
        # Check if vote already exists
        existing_vote = db.exec(select(Vote).where(
            (Vote.post_id == post_id) & (Vote.user_id == current_user.id)
        )).first()
        
        if existing_vote:
            # Remove vote if it exists
            db.delete(existing_vote)
            db.commit()
            return {"message": "Vote removed from post"}
        else:
            # Add new vote
            new_vote = Vote(post_id=post_id, user_id=current_user.id)
            db.add(new_vote)
            db.commit()
            return {"message": "Vote added to post"}
    
    # Handle reel vote
    else:
        reel_id = vote_request.reel_id
        
        # Check if reel exists
        reel = db.get(Reel, reel_id)
        if not reel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reel not found")
            
        # Check if vote already exists
        existing_vote = db.exec(select(Vote).where(
            (Vote.reel_id == reel_id) & (Vote.user_id == current_user.id)
        )).first()
        
        if existing_vote:
            # Remove vote if it exists
            db.delete(existing_vote)
            db.commit()
            return {"message": "Vote removed from reel"}
        else:
            # Add new vote
            new_vote = Vote(reel_id=reel_id, user_id=current_user.id)
            db.add(new_vote)
            db.commit()
            return {"message": "Vote added to reel"}