from sqlmodel import Relationship, SQLModel, Field
from datetime import datetime
from typing import Optional, List
from pydantic import EmailStr, field_validator, ValidationInfo

import re
class PostBase(SQLModel):
    title: str
    content: str
    # published is optional, default to True if not provided
    published: Optional[bool] = True


class Post(PostBase, table=True):
    # id is optional, primary key, auto-incremented by database
    id: Optional[int] = Field(default=None, primary_key=True)
    # created_at is automatically set to the current time (UTC)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    owner_id: int = Field(foreign_key="user.id", nullable=False)
    owner: Optional["User"] = Relationship(back_populates="posts")
    
    # Updated votes relationship to use the unified Vote model
    votes: List["PostVote"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Post.id==PostVote.post_id",
            "cascade": "all, delete-orphan"
        }
    )

    
    comments: List["Comment"] = Relationship(
        back_populates="post",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    id: int
    created_at: datetime
    owner_id : int
    votes: int = 0


class UserBase(SQLModel):
    username: str = Field(index=True)
    email: EmailStr = Field(unique=True, index=True)
    phone_number: Optional[int] = Field(unique=True, nullable=True)
    profile_picture: Optional[str] = None  # URL to profile picture
    background_image: Optional[str] = None  # URL to background image    
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    posts: List["Post"] = Relationship(back_populates="owner")
    followers: List["Follow"] = Relationship(sa_relationship_kwargs={"primaryjoin": "User.id==Follow.following_id", "overlaps": "following"})
    following: List["Follow"] = Relationship(sa_relationship_kwargs={"primaryjoin": "User.id==Follow.follower_id", "overlaps": "followers"})
    comments: List["Comment"] = Relationship(back_populates="user")
    reels: List["Reel"] = Relationship(back_populates="owner")

class UserCreate(UserBase):
    password: str
    password_confirm: str
    
    @field_validator('password')
    def password_strength(cls, v):
        """Validate password strength"""
        min_length = 8
        
        if len(v) < min_length:
            raise ValueError(f'Password must be at least {min_length} characters')
            
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
            
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
            
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
            
        if not re.search(r'[^A-Za-z0-9]', v):
            raise ValueError('Password must contain at least one special character')
            
        return v
    
    @field_validator("password_confirm")
    def passwords_match(cls, v, info: ValidationInfo):
        password = info.data.get("password") if info.data else None
        if password and v != password:
            raise ValueError("Passwords do not match")
        return v

class UserResponse(UserBase):
    id: int
    created_at: datetime

class UserInfo(SQLModel):
    id: int
    username: str

class PostWithOwnerResponse(PostResponse):
    owner: UserInfo

class PostVote(SQLModel, table=True):
    user_id: int = Field(primary_key=True, foreign_key="user.id", ondelete="CASCADE")
    post_id: int = Field(primary_key=True, foreign_key="post.id", ondelete="CASCADE")

class ReelVote(SQLModel, table=True):
    user_id: int = Field(primary_key=True, foreign_key="user.id", ondelete="CASCADE")
    reel_id: int = Field(primary_key=True, foreign_key="reel.id", ondelete="CASCADE")


# Add to model.py
class ReelBase(SQLModel):
    title: str
    description: Optional[str] = None
    video_url: str  # URL to the stored video file
    thumbnail_url: Optional[str] = None  # URL to thumbnail image
    duration: int  # Duration in seconds (max of 110 seconds = 1:50 mins)

class Reel(ReelBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    owner_id: int = Field(foreign_key="user.id", nullable=False)
    owner: Optional["User"] = Relationship(back_populates="reels")
    
    # Relationships using existing models
    votes: List["ReelVote"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Reel.id==ReelVote.reel_id",
            "cascade": "all, delete-orphan"
        }
    )
    comments: List["Comment"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Reel.id==Comment.reel_id",
            "cascade": "all, delete-orphan"
        }
    )

class ReelCreate(ReelBase):
    pass

class ReelResponse(ReelBase):
    id: int
    created_at: datetime
    owner_id: int
    votes: int = 0

class ReelWithOwnerResponse(ReelResponse):
    owner: UserInfo
# New models for Follow functionality
class Follow(SQLModel, table=True):
    follower_id: int = Field(ondelete="CASCADE", primary_key=True, foreign_key="user.id")
    following_id: int = Field(ondelete="CASCADE", primary_key=True, foreign_key="user.id")

class FollowResponse(SQLModel):
    follower_id: int
    following_id: int
    follower: UserInfo
    following: UserInfo

# New models for Comment functionality
class CommentBase(SQLModel):
    content: str

class Comment(CommentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    
    # Make post_id optional to allow comments on either posts or reels
    post_id: Optional[int] = Field(default=None, foreign_key="post.id", ondelete="CASCADE", nullable=True)
    reel_id: Optional[int] = Field(default=None, foreign_key="reel.id", ondelete="CASCADE", nullable=True)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="comments")
    post: Optional["Post"] = Relationship(back_populates="comments")
    reel: Optional["Reel"] = Relationship(back_populates="comments")
    
    # Validator to ensure either post_id or reel_id is set but not both
    @field_validator('reel_id')
    def validate_comment_target(cls, v, info: ValidationInfo):
        post_id = info.data.get("post_id") if info.data else None
        if (post_id is None and v is None) or (post_id is not None and v is not None):
            raise ValueError("Either post_id or reel_id must be set, but not both")
        return v

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    created_at: datetime
    user_id: int
    post_id: Optional[int] = None
    reel_id: Optional[int] = None
    user: UserInfo

from pydantic import BaseModel, field_validator, ValidationInfo

class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    phone_number: Optional[int] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None
    
    @field_validator('email')
    def validate_email(cls, v):
        # Reuse your existing email validation logic or add specific checks
        if v and not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError('Invalid email format')
        return v
    
    @field_validator('new_password')
    def validate_password(cls, v):
        """
        Reuse the password validation logic from UserCreate
        """
        if v:
            min_length = 8
            
            if len(v) < min_length:
                raise ValueError(f'Password must be at least {min_length} characters')
                
            if not re.search(r'[A-Z]', v):
                raise ValueError('Password must contain at least one uppercase letter')
                
            if not re.search(r'[a-z]', v):
                raise ValueError('Password must contain at least one lowercase letter')
                
            if not re.search(r'[0-9]', v):
                raise ValueError('Password must contain at least one number')
                
            if not re.search(r'[^A-Za-z0-9]', v):
                raise ValueError('Password must contain at least one special character')
        
        return v