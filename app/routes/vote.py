from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select,SQLModel
from app.database import get_session
from app.model import Post, Vote, User
from .auth import get_current_user
from typing import Optional

router = APIRouter(
    prefix="/vote",
    tags=["votes"]
)

class VoteRequest(SQLModel):
    post_id: int

@router.post("/", status_code=status.HTTP_201_CREATED)
def vote(
    vote: VoteRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    post_id = vote.post_id

    post = db.exec(select(Post).where(Post.id == post_id)).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    existing_vote = db.exec(select(Vote).where(
        (Vote.post_id == post_id) & (Vote.user_id == current_user.id)
    )).first()

    if existing_vote:
        db.delete(existing_vote)
        db.commit()
        return {"message": "Vote removed"}
    else:
        new_vote = Vote(post_id=post_id, user_id=current_user.id)
        db.add(new_vote)
        db.commit()
        return {"message": "Vote added"}
