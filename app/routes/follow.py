from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.model import User, Follow, UserInfo, FollowResponse
from app.routes.auth import get_current_user

# Corrected: Use a simple prefix that matches the expected URLs
router = APIRouter(
    prefix="/users",  # This will make endpoints available at /users/follow, /users/followers, etc.
    tags=["follow"]
)

@router.post("/follow/{user_id}", status_code=status.HTTP_201_CREATED)
def follow_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Check if the user exists
    user_to_follow = session.get(User, user_id)
    if not user_to_follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # Check if trying to follow self
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot follow yourself"
        )

    # Check if already following
    existing_follow = session.exec(
        select(Follow).where(
            (Follow.follower_id == current_user.id) & 
            (Follow.following_id == user_id)
        )
    ).first()

    if existing_follow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You are already following user with ID {user_id}"
        )

    # Create new follow relationship
    new_follow = Follow(follower_id=current_user.id, following_id=user_id)
    session.add(new_follow)
    session.commit()

    return {"message": f"You are now following user with ID {user_id}"}

@router.post("/unfollow/{user_id}", status_code=status.HTTP_200_OK)
def unfollow_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Check if the user exists
    user_to_unfollow = session.get(User, user_id)
    if not user_to_unfollow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # Find the follow relationship
    follow = session.exec(
        select(Follow).where(
            (Follow.follower_id == current_user.id) & 
            (Follow.following_id == user_id)
        )
    ).first()

    if not follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"You are not following user with ID {user_id}"
        )

    # Remove the follow relationship
    session.delete(follow)
    session.commit()

    return {"message": f"You have unfollowed user with ID {user_id}"}

@router.get("/followers", response_model=list[UserInfo])
def get_followers(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Get followers of the current user
    query = select(User).join(
        Follow, 
        (Follow.follower_id == User.id) & 
        (Follow.following_id == current_user.id)
    )
    
    followers = session.exec(query).all()
    
    return [UserInfo(id=follower.id, username=follower.username) for follower in followers]

@router.get("/following", response_model=list[UserInfo])
def get_following(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Get users that the current user is following
    query = select(User).join(
        Follow, 
        (Follow.following_id == User.id) & 
        (Follow.follower_id == current_user.id)
    )
    
    following = session.exec(query).all()
    
    return [UserInfo(id=user.id, username=user.username) for user in following]