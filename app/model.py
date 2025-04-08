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
    votes: List["Vote"] = Relationship(sa_relationship_kwargs={"primaryjoin": "Post.id==Vote.post_id"})
    comments: List["Comment"] = Relationship(back_populates="post")
    
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
    phone_number: int = Field(unique=True, nullable=False)

    
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    posts: List["Post"] = Relationship(back_populates="owner")
    followers: List["Follow"] = Relationship(sa_relationship_kwargs={"primaryjoin": "User.id==Follow.following_id", "overlaps": "following"})
    following: List["Follow"] = Relationship(sa_relationship_kwargs={"primaryjoin": "User.id==Follow.follower_id", "overlaps": "followers"})
    comments: List["Comment"] = Relationship(back_populates="user")

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

class Vote(SQLModel, table=True):
    user_id: int = Field(ondelete="CASCADE", primary_key=True, foreign_key="user.id")
    post_id: int = Field(ondelete="CASCADE", primary_key=True, foreign_key="post.id")

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
    post_id: int = Field(foreign_key="post.id", nullable=False)
    user: Optional["User"] = Relationship(back_populates="comments")
    post: Optional["Post"] = Relationship(back_populates="comments")

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    created_at: datetime
    user_id: int
    post_id: int
    user: UserInfo