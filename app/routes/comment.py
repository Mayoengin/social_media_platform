from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.model import Post, Comment, CommentCreate, CommentResponse, User, UserInfo
from app.routes.auth import get_current_user

router = APIRouter(
    prefix="/posts",
    tags=["comments"]
)

@router.post("/{post_id}/comment", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
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
        user=user_info
    )
    
    return comment_response

@router.get("/{post_id}/comments", response_model=list[CommentResponse])
def get_comments(
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
            user=user_info
        )
        
        comments_response.append(comment_response)
    
    return comments_response