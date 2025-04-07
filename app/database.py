from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.exc import SQLAlchemyError
from .config import settings
DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
engine = create_engine(DATABASE_URL, echo=True)

# Function to create tables based on defined models
def create_db_and_tables():
    try:
        # Creating tables from all models (like Post)
        print("Creating tables...")
        SQLModel.metadata.create_all(engine)
        print("Tables created successfully!")
    except SQLAlchemyError as e:
        print(f"Error while creating tables: {e}")

# Create a session for use as a dependency
def get_session():
    with Session(engine) as session:
        yield session