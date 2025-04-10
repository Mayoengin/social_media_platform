from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status, 
    File, 
    UploadFile
)
from sqlmodel import Session, select
from app.database import get_session
from app.model import (
    User, 
    UserCreate, 
    UserResponse, 
    UserUpdateRequest
)
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm
from .auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from datetime import timedelta
import re
import os
import uuid
import shutil
# Import the file upload service
from app.services.file_upload import save_uploaded_file, get_file_url

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    # Check if email already exists
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user (without password_confirm field)
    new_user = User(
        username=user.username,
        email=user.email,
        password=pwd_context.hash(user.password), # Hash the password
        phone_number=user.phone_number
    )
    
    # Add and commit to database
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return new_user

@router.get("/", response_model=list[UserResponse])
def get_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get the current user's profile"""
    return current_user

@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    user_update: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    try:
        # Validate and update email if provided
        if user_update.email:
            # Check if email is already taken by another user
            existing_email_user = session.exec(
                select(User).where(User.email == user_update.email)
            ).first()
            
            if existing_email_user and existing_email_user.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered to another user"
                )
            
            current_user.email = user_update.email
        
        # Update phone number if provided
        if user_update.phone_number is not None:
            # Check if phone number is already taken by another user
            existing_phone_user = session.exec(
                select(User).where(User.phone_number == user_update.phone_number)
            ).first()
            
            if existing_phone_user and existing_phone_user.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number already registered to another user"
                )
            
            current_user.phone_number = user_update.phone_number
        
        # Handle password change
        if user_update.new_password:
            # Verify current password is provided and correct
            if not user_update.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required to change password"
                )
            
            # Verify current password matches
            if not pwd_context.verify(user_update.current_password, current_user.password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Hash and update to new password
            current_user.password = pwd_context.hash(user_update.new_password)
        
        # Commit changes
        session.commit()
        session.refresh(current_user)
        
        return current_user
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Rollback in case of any unexpected errors
        session.rollback()
        # Log the error for debugging
        print(f"Unexpected error during profile update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating profile"
        )

@router.get("/id/{user_id}", response_model=UserResponse)
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")
    return user

@router.get("/username/{username}", response_model=UserResponse)
def get_user_by_name(username: str, session: Session = Depends(get_session)):
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with username '{username}' not found")
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserCreate, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")
    
    # Check if email already exists and belongs to a different user
    if user_data.email != user.email:
        existing_user = session.exec(select(User).where(User.email == user_data.email)).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered to another user"
            )
    
    # Update user data
    user.username = user_data.username
    user.email = user_data.email
    user.password = pwd_context.hash(user_data.password)
    
    session.commit()
    session.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")
    session.delete(user)
    session.commit()
    return

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    print(f"Login attempt for username: {form_data.username}")
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        print(f"Authentication failed for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    print(f"Successful login for username: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}
@router.post("/upload-profile-picture", response_model=UserResponse)
def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    try:
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPEG, PNG, and GIF are allowed."
            )
       
        # Define upload directory - make absolute path
        upload_dir = os.path.join(os.getcwd(), "static", "profile_pictures")
       
        # Ensure directory exists
        os.makedirs(upload_dir, exist_ok=True)
       
        # Generate a unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
       
        # Log the file path for debugging
        print(f"Saving file to: {file_path}")
       
        # Save the file directly
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as save_error:
            print(f"File save error: {save_error}")
            raise
           
        # Generate file URL with full domain
        # Replace with your actual backend URL or use config
        backend_url = "//social-media-platform-jgf2.onrender.com"  # Update this to your actual URL
        file_url = f"{backend_url}/static/profile_pictures/{unique_filename}"
        print(f"File URL: {file_url}")
       
        # Update user's profile picture
        current_user.profile_picture = file_url
        session.commit()
        session.refresh(current_user)
       
        return current_user
   
    except Exception as e:
        # Log the full error for debugging
        import traceback
        print(f"Error uploading profile picture: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )
   
@router.post("/upload-background-image", response_model=UserResponse)
def upload_background_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    try:
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPEG, PNG, and GIF are allowed."
            )
       
        # Define upload directory - make absolute path
        upload_dir = os.path.join(os.getcwd(), "static", "background_images")
       
        # Ensure directory exists
        os.makedirs(upload_dir, exist_ok=True)
       
        # Generate a unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
       
        # Save the file directly
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as save_error:
            print(f"File save error: {save_error}")
            raise
           
        # Generate file URL with full domain
        # Replace with your actual backend URL or use config
        backend_url = "//social-media-platform-jgf2.onrender.com"  # Update this to your actual URL
        file_url = f"{backend_url}/static/background_images/{unique_filename}"
       
        # Update user's background image
        current_user.background_image = file_url
        session.commit()
        session.refresh(current_user)
       
        return current_user
   
    except Exception as e:
        import traceback
        print(f"Error uploading background image: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload background image: {str(e)}"
        )