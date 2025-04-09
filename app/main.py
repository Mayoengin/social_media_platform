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

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add CORS middleware
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://mayoengin.github.io",
    "https://mayoengin.github.io/social_media_platform-frontend/"
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

# Include routers
app.include_router(posts_router)
app.include_router(users_router)
app.include_router(vote_router)
app.include_router(follow_router)
app.include_router(comment_router)
app.include_router(reels_router)  # Add this line

@app.get("/")
def root():
    return {"message": "Hello World"}

# Optional: Initialize database on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()