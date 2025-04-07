from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.model import Post, PostCreate, PostResponse, User,PostWithOwnerResponse,Vote,UserInfo
from .auth import get_current_user  # Import the authentication dependency
from typing import Optional
from sqlalchemy import func


router = APIRouter(
    prefix="/posts",
    tags=["posts"]
)
@router.get("/", response_model=list[PostWithOwnerResponse])
def get_posts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    skip: int = 0,
    search: Optional[str] = ""
):
    # Join Post with User and count votes
    query = select(
        Post, 
        func.count(Vote.post_id).label("votes")
    ).join(
        User, 
        Post.owner_id == User.id, 
        isouter=False  # Inner join as every post must have an owner
    ).join(
        Vote, 
        Vote.post_id == Post.id, 
        isouter=True  # Left outer join as posts might not have votes
    ).group_by(
        Post.id
    )
    
    if search:
        query = query.filter(Post.title.contains(search))
    
    # Apply pagination
    results = session.exec(query.offset(skip).limit(limit)).all()
    
    # Format the results
    posts_with_details = []
    for post, votes in results:
        # Get the owner separately to ensure we get the right structure
        owner = session.get(User, post.owner_id)
        owner_info = UserInfo(id=owner.id, username=owner.username)
        
        # Create the response object
        post_response = PostWithOwnerResponse(
            id=post.id,
            title=post.title,
            content=post.content,
            published=post.published,
            created_at=post.created_at,
            owner_id=post.owner_id,
            votes=votes,
            owner=owner_info
        )
        
        posts_with_details.append(post_response)
    
    return posts_with_details
@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    post: PostCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Create new post for the current logged-in user
    new_post = Post(**post.dict(), owner_id=current_user.id)  # Link the post to the current user
    session.add(new_post)
    session.commit()
    session.refresh(new_post)
    return new_post

@router.get("/latest", response_model=PostWithOwnerResponse)
def get_latest_post(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Query that joins Post with Vote to count votes for the latest post
    query = select(
        Post, 
        func.count(Vote.post_id).label("votes")
    ).join(
        Vote, 
        Vote.post_id == Post.id, 
        isouter=True
    ).group_by(
        Post.id
    ).order_by(Post.id.desc()).limit(1)
    
    result = session.exec(query).first()
    
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No posts found")
    
    post, votes = result
    
    # Get the owner
    owner = session.get(User, post.owner_id)
    owner_info = UserInfo(id=owner.id, username=owner.username)
    
    # Create the response with owner and votes
    post_response = PostWithOwnerResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        published=post.published,
        created_at=post.created_at,
        owner_id=post.owner_id,
        votes=votes,
        owner=owner_info
    )
    
    return post_response

@router.get("/{id}", response_model=PostWithOwnerResponse)
def get_post_by_id(
    id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Query that joins Post with Vote to count votes for the specific post
    query = select(
        Post, 
        func.count(Vote.post_id).label("votes")
    ).join(
        Vote, 
        Vote.post_id == Post.id, 
        isouter=True
    ).filter(Post.id == id).group_by(Post.id)
    
    result = session.exec(query).first()
    
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No post with ID {id}")
    
    post, votes = result
    
    # Get the owner
    owner = session.get(User, post.owner_id)
    owner_info = UserInfo(id=owner.id, username=owner.username)
    
    # Create the response with owner and votes
    post_response = PostWithOwnerResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        published=post.published,
        created_at=post.created_at,
        owner_id=post.owner_id,
        votes=votes,
        owner=owner_info
    )
    
    return post_response

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Retrieve post by ID
    post = session.get(Post, id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with ID {id} not found")
    
    # Check if the current user is the owner of the post
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")
    
    session.delete(post)
    session.commit()
    return

@router.put("/{id}", response_model=PostResponse)
def update_post(
    id: int,
    updated_post: PostCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Retrieve post by ID
    post = session.get(Post, id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with ID {id} not found")
    
    # Check if the current user is the owner of the post
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")
    
    # Update post fields
    post.title = updated_post.title
    post.content = updated_post.content
    post.published = updated_post.published

    session.commit()
    session.refresh(post)
    return post
