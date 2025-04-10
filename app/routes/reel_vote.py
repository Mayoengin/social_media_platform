from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, SQLModel
from app.database import get_session
from app.model import Reel, ReelVote, User
from app.routes.auth import get_current_user
from typing import Optional

router = APIRouter(
    prefix="/reels",
    tags=["reel_votes"]
)

class ReelVoteRequest(SQLModel):
    reel_id: int
from sqlalchemy import func

@router.post("/like", status_code=status.HTTP_201_CREATED)
def vote_reel(
    vote_request: ReelVoteRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Check if reel exists
    reel = db.get(Reel, vote_request.reel_id)
    if not reel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reel not found")
       
    # Check if vote already exists
    existing_vote = db.exec(select(ReelVote).where(
        (ReelVote.reel_id == vote_request.reel_id) &
        (ReelVote.user_id == current_user.id)
    )).first()
   
    if existing_vote:
        # Remove vote if it exists
        db.delete(existing_vote)
        db.commit()
    else:
        # Add new vote
        new_vote = ReelVote(reel_id=vote_request.reel_id, user_id=current_user.id)
        db.add(new_vote)
        db.commit()
    
    # Count total votes for this reel
    vote_count = db.exec(
        select(func.count()).where(ReelVote.reel_id == vote_request.reel_id)
    ).one()
    
    # Determine if current user has liked the reel
    user_vote = db.exec(
        select(ReelVote).where(
            (ReelVote.reel_id == vote_request.reel_id) & 
            (ReelVote.user_id == current_user.id)
        )
    ).first()
    
    return {
        "message": "Vote toggled" if existing_vote else "Vote added",
        "votes": vote_count,
        "is_liked": user_vote is not None
    }