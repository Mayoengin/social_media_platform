from sqlmodel import Relationship, SQLModel, Field
from datetime import datetime
from typing import Optional
from pydantic import EmailStr, field_validator,ValidationInfo

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
    phone_number: int = Field(unique=True,nullable=False)

    
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    posts: list["Post"] = Relationship(back_populates="owner")

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

class Vote(SQLModel,table=True):

    user_id: int= Field(ondelete="CASCADE", primary_key=True,foreign_key="user.id")
    post_id: int = Field(ondelete="CASCADE", primary_key=True,foreign_key="post.id")
