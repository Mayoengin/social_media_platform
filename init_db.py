from app.database import create_db_and_tables
from app.model import Post  # Import needed to register model with SQLModel

if __name__ == "__main__":
    create_db_and_tables()