from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.model import Post, Reel, Comment, CommentCreate, CommentResponse, User, UserInfo
from app.routes.auth import get_current_user

router = APIRouter(
    tags=["comments"]
)

# Post comments
@router.post("/posts/{post_id}/comment", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_post_comment(
    post_id: int,
    comment: CommentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Check if post exists
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found"
        )
    
    # Create new comment
    new_comment = Comment(
        content=comment.content,
        post_id=post_id,
        user_id=current_user.id
    )
    
    session.add(new_comment)
    session.commit()
    session.refresh(new_comment)
    
    # Create UserInfo for response
    user_info = UserInfo(id=current_user.id, username=current_user.username)
    
    # Create CommentResponse
    comment_response = CommentResponse(
        id=new_comment.id,
        content=new_comment.content,
        created_at=new_comment.created_at,
        user_id=new_comment.user_id,
        post_id=new_comment.post_id,
        reel_id=None,
        user=user_info
    )
    
    return comment_response

@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
def get_post_comments(
    post_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Check if post exists
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found"
        )
    
    # Get comments for the post
    query = select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at)
    comments = session.exec(query).all()
    
    # Create response with user info
    comments_response = []
    for comment in comments:
        user = session.get(User, comment.user_id)
        user_info = UserInfo(id=user.id, username=user.username)
        
        comment_response = CommentResponse(
            id=comment.id,
            content=comment.content,
            created_at=comment.created_at,
            user_id=comment.user_id,
            post_id=comment.post_id,
            reel_id=None,
            user=user_info
        )
        
        comments_response.append(comment_response)
    
    return comments_response

# Reel comments
@router.post("/reels/{reel_id}/comment", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_reel_comment(
    reel_id: int,
    comment: CommentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Check if reel exists
    reel = session.get(Reel, reel_id)
    if not reel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reel with ID {reel_id} not found"
        )
    
    # Create new comment
    new_comment = Comment(
        content=comment.content,
        reel_id=reel_id,
        user_id=current_user.id
    )
    
    session.add(new_comment)
    session.commit()
    session.refresh(new_comment)
    
    # Create UserInfo for response
    user_info = UserInfo(id=current_user.id, username=current_user.username)
    
    # Create CommentResponse
    comment_response = CommentResponse(
        id=new_comment.id,
        content=new_comment.content,
        created_at=new_comment.created_at,
        user_id=new_comment.user_id,
        post_id=None,
        reel_id=new_comment.reel_id,
        user=user_info
    )
    
    return comment_response

@router.get("/reels/{reel_id}/comments", response_model=list[CommentResponse])
def get_reel_comments(
    reel_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Check if reel exists
    reel = session.get(Reel, reel_id)
    if not reel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reel with ID {reel_id} not found"
        )
    
    # Get comments for the reel
    query = select(Comment).where(Comment.reel_id == reel_id).order_by(Comment.created_at)
    comments = session.exec(query).all()
    
    # Create response with user info
    comments_response = []
    for comment in comments:
        user = session.get(User, comment.user_id)
        user_info = UserInfo(id=user.id, username=user.username)
        
        comment_response = CommentResponse(
            id=comment.id,
            content=comment.content,
            created_at=comment.created_at,
            user_id=comment.user_id,
            post_id=None,
            reel_id=comment.reel_id,
            user=user_info
        )
        
        comments_response.append(comment_response)
    
    return comments_response