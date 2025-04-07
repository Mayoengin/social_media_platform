from fastapi import FastAPI
from app.routes.posts import router as posts_router
from app.routes.users import router as users_router
from app.routes.vote import router as vote_router
from app.database import create_db_and_tables
from .config import settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://your-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(posts_router)
app.include_router(users_router)
app.include_router(vote_router)

@app.get("/")
def root():
    return {"message": "Hello World"}

# Optional: Initialize database on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
