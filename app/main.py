from fastapi import FastAPI
from app.routes.posts import router as posts_router
from app.routes.users import router as users_router
from app.routes.vote import router as vote_router
from app.routes.follow import router as follow_router
from app.routes.comment import router as comment_router
from app.routes.reel import router as reels_router  # Add this import
from app.database import create_db_and_tables
from .config import settings
from fastapi.middleware.cors import CORSMiddleware
import logging
from fastapi.staticfiles import StaticFiles  # Add this import
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.routes.reel_vote import router as reel_vote_router
app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add CORS middleware
origins = [
    "https://mayoengin.github.io/social_media_platform-frontend/",
    "http://localhost:8080",
    "http://localhost:8081",  # Add the correct port your frontend is using
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",  # Also add the IP version
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://mayoengin.github.io"
  
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory for serving uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
os.makedirs("static", exist_ok=True)
os.makedirs("static/profile_pictures", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
# Include routers
app.include_router(posts_router)
app.include_router(users_router)
app.include_router(vote_router)
app.include_router(follow_router)
app.include_router(comment_router)
app.include_router(reels_router)  
app.include_router(reel_vote_router)
@app.get("/")
def root():
    return {"message": "Hello World"}

# Optional: Initialize database on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()